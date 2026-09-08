import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from docx import Document

from src.schema import ALIASES
from src.data_utils import best_alias_map, dataframe_to_records_text
from src.analytics import build_analysis
from src.rag_engine import build_faiss_index
from src.gemini_client import is_auth_error, is_transient_error
from src.state import invalidate_api_key

SUPPORTED = ["csv", "xlsx", "xls", "json", "txt", "md", "pdf", "docx"]

def _read_file(uploaded):
    ext = Path(uploaded.name).suffix.lower()
    data = uploaded.getvalue()
    tables, texts = {}, []

    if ext == ".csv":
        tables[uploaded.name] = pd.read_csv(io.BytesIO(data))
    elif ext in (".xlsx", ".xls"):
        book = pd.read_excel(io.BytesIO(data), sheet_name=None)
        for sheet, df in book.items():
            tables[f"{uploaded.name}::{sheet}"] = df
    elif ext == ".json":
        obj = json.loads(data.decode("utf-8", errors="ignore"))
        if isinstance(obj, list):
            tables[uploaded.name] = pd.json_normalize(obj)
        elif isinstance(obj, dict):
            try:
                tables[uploaded.name] = pd.json_normalize(obj)
            except Exception:
                texts.append(
                    (uploaded.name, json.dumps(obj, ensure_ascii=False, indent=2))
                )
    elif ext in (".txt", ".md"):
        texts.append((uploaded.name, data.decode("utf-8", errors="ignore")))
    elif ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        texts.append((uploaded.name, text))
    elif ext == ".docx":
        doc = Document(io.BytesIO(data))
        paragraphs = "\n".join(
            p.text for p in doc.paragraphs if p.text.strip()
        )
        if paragraphs.strip():
            texts.append((uploaded.name, paragraphs))

        for t_idx, table in enumerate(doc.tables, 1):
            rows = [[cell.text for cell in row.cells] for row in table.rows]
            if len(rows) >= 2 and any(str(x).strip() for x in rows[0]):
                tables[f"{uploaded.name}::table_{t_idx}"] = pd.DataFrame(
                    rows[1:], columns=rows[0]
                )
    else:
        raise ValueError(f"Unsupported file type: {ext or 'unknown'}")

    return tables, texts

def _normalize_tables(raw_tables):
    normalized_tables = {}
    for name, df in raw_tables.items():
        if df is None:
            continue

        df = df.copy()
        if len(df.columns) == 0:
            normalized_tables[name] = df
            continue

        df.columns = [str(c).strip() for c in df.columns]
        mapping = best_alias_map(df.columns, ALIASES)
        df = df.rename(columns=mapping)
        normalized_tables[name] = df

    return normalized_tables

def _quality_report(tables):
    columns = set()
    nonempty_rows = 0

    for df in tables.values():
        columns.update(df.columns)
        nonempty_rows += len(df)

    checks = {
        "Quarter target": any(c in columns for c in ("quarter_target", "quarter")),
        "Production line": "line_id" in columns,
        "Line supervisor": "supervisor" in columns,
        "Weekly target": "target_units" in columns,
        "Actual production": "actual_units" in columns,
        "Machine ID": "machine_id" in columns,
        "Machine issue": "issue" in columns,
        "Downtime": ("downtime_minutes" in columns) or ("downtime_hours" in columns),
        "Defects / rejects": "defect_units" in columns,
    }

    found = [k for k, v in checks.items() if v]
    missing = [k for k, v in checks.items() if not v]

    return {
        "checks": checks,
        "found": found,
        "missing": missing,
        "score": round(100 * len(found) / len(checks)),
        "recognized_columns": sorted(columns),
        "row_count": nonempty_rows,
    }

def _make_chunks(tables, texts):
    chunks = []
    metadata = []

    for name, df in tables.items():
        if df is None or df.empty:
            continue
        for text in dataframe_to_records_text(name, df):
            chunks.append(text)
            metadata.append({"source": name, "type": "table_row"})

    for name, text in texts:
        clean = " ".join((text or "").split())
        if not clean:
            continue

        size = 1100
        overlap = 150
        start = 0

        while start < len(clean):
            chunk = clean[start:start + size]
            if chunk.strip():
                chunks.append(f"Source document {name}. {chunk}")
                metadata.append({"source": name, "type": "document_text"})

            if start + size >= len(clean):
                break
            start += size - overlap

    return chunks, metadata

def _store_processed_state(raw_tables, raw_texts, normalized, quality, analysis,
                           chunks, metadata, file_summary):
    st.session_state.raw_tables = raw_tables
    st.session_state.raw_texts = raw_texts
    st.session_state.normalized = normalized
    st.session_state.quality_report = quality
    st.session_state.analysis = analysis
    st.session_state.chunks = chunks
    st.session_state.chunk_metadata = metadata
    st.session_state.file_summary = file_summary
    # Even incomplete/empty-ish files count as processed. The dashboard must
    # degrade gracefully instead of crashing.
    st.session_state.data_ready = True

def _try_build_index(chunks):
    st.session_state.faiss_index = None
    st.session_state.rag_ready = False
    st.session_state.embedding_error = None

    if not chunks:
        st.session_state.embedding_error = (
            "No searchable text rows were extracted. Dashboard analysis is still available "
            "for any recognized structured fields, but RAG search cannot be built."
        )
        return

    try:
        st.session_state.faiss_index = build_faiss_index(
            st.session_state.client,
            chunks,
        )
        st.session_state.rag_ready = True
    except Exception as exc:
        if is_auth_error(exc):
            invalidate_api_key(f"Gemini authentication failed: {exc}")
            st.rerun()

        st.session_state.embedding_error = (
            "The files were analyzed, but the FAISS index could not be built right now. "
            f"Reason: {exc}"
        )

def render_upload_and_process():
    st.markdown("## Upload factory data")
    st.caption(
        "Supported: CSV, Excel, JSON, TXT, Markdown, PDF and DOCX. "
        "Incomplete files are allowed; missing fields are reported instead of crashing the app."
    )

    uploads = st.file_uploader(
        "Drop production, target, line, supervisor or machine-log files here",
        type=SUPPORTED,
        accept_multiple_files=True,
    )

    if not uploads:
        st.info(
            "No files selected yet. The app will remain usable; choose files when you are ready."
        )
    else:
        st.write(f"**{len(uploads)} file(s) selected**")
        for f in uploads:
            st.caption(f"• {f.name} — {f.size / 1024:.1f} KB")

        if st.button(
            "Analyze & build knowledge index",
            type="primary",
            use_container_width=True,
        ):
            raw_tables, raw_texts, file_summary = {}, [], []

            try:
                with st.status("Processing factory data…", expanded=True) as status:
                    for up in uploads:
                        st.write(f"Reading **{up.name}**")
                        try:
                            tables, texts = _read_file(up)
                            raw_tables.update(tables)
                            raw_texts.extend(texts)
                            file_summary.append({
                                "name": up.name,
                                "tables": len(tables),
                                "text_docs": len(texts),
                                "status": "read",
                            })
                        except Exception as file_exc:
                            file_summary.append({
                                "name": up.name,
                                "tables": 0,
                                "text_docs": 0,
                                "status": f"error: {file_exc}",
                            })
                            st.warning(f"{up.name}: {file_exc}")

                    st.write("Normalizing fields")
                    normalized = _normalize_tables(raw_tables)

                    st.write("Checking data sufficiency")
                    quality = _quality_report(normalized)

                    st.write("Calculating available analytics")
                    analysis = build_analysis(normalized)

                    st.write("Creating searchable chunks")
                    chunks, metadata = _make_chunks(normalized, raw_texts)

                    # Store the useful work BEFORE embeddings. An embedding/API
                    # failure must not throw away the dashboard analysis.
                    _store_processed_state(
                        raw_tables, raw_texts, normalized, quality,
                        analysis, chunks, metadata, file_summary,
                    )

                    st.write("Building FAISS index when possible")
                    _try_build_index(chunks)

                    status.update(
                        label="Factory files processed",
                        state="complete",
                        expanded=False,
                    )

                st.success("Files processed. Open Dashboard to review the results.")

                if st.session_state.embedding_error:
                    st.warning(st.session_state.embedding_error)

            except Exception as exc:
                if is_auth_error(exc):
                    invalidate_api_key(f"Gemini authentication failed: {exc}")
                    st.rerun()

                # Last-resort guard: do not kill the app.
                st.error(f"Some processing failed: {exc}")
                st.info(
                    "The app is still running. Check the file format/columns or upload another file."
                )

    if st.session_state.data_ready:
        st.divider()
        q = st.session_state.quality_report or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Data readiness", f"{q.get('score', 0)}%")
        c2.metric("Rows detected", f"{q.get('row_count', 0):,}")
        c3.metric("Searchable chunks", f"{len(st.session_state.chunks):,}")

        if st.session_state.rag_ready:
            st.success("FAISS RAG index is ready.", icon="✅")
        elif st.session_state.embedding_error:
            st.warning(st.session_state.embedding_error)

        with st.expander("Detected and missing information", expanded=True):
            for label, ok in q.get("checks", {}).items():
                st.write(("✅" if ok else "⚠️") + " " + label)

        if (
            not st.session_state.rag_ready
            and st.session_state.chunks
            and st.button("Retry FAISS index", use_container_width=True)
        ):
            with st.spinner("Retrying embeddings and FAISS…"):
                _try_build_index(st.session_state.chunks)
            st.rerun()
