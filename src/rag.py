import json
import streamlit as st

from src.rag_engine import retrieve
from src.gemini_client import (
    generate_text,
    is_auth_error,
    GeminiTransientError,
    GeminiModelUnavailableError,
)
from src.state import invalidate_api_key, mark_model_unavailable

SUGGESTED = [
    "Which production line is furthest behind target?",
    "Which machine is causing the most downtime?",
    "What should the production manager prioritize this week?",
    "Are any machine issues recurring on underperforming lines?",
]

def _calculated_context():
    a = st.session_state.analysis or {}
    line = a.get("line_summary")
    machine = a.get("machine_summary")

    return {
        "kpis": a.get("kpis", {}),
        "line_summary": (
            [] if line is None or line.empty
            else line.head(20).to_dict(orient="records")
        ),
        "machine_summary": (
            [] if machine is None or machine.empty
            else machine.head(20).to_dict(orient="records")
        ),
        "deterministic_findings": a.get("deterministic_findings", []),
        "data_quality": st.session_state.quality_report or {},
    }

def answer_question(question):
    hits = []

    if st.session_state.rag_ready and st.session_state.faiss_index is not None:
        hits = retrieve(
            st.session_state.client,
            st.session_state.faiss_index,
            st.session_state.chunks,
            st.session_state.chunk_metadata,
            question,
            k=10,
        )

    retrieved = "\n\n".join(
        f"[{i + 1}] {h['text']}" for i, h in enumerate(hits)
    )
    calc = json.dumps(_calculated_context(), default=str)

    prompt = f"""
You are FactoryOps AI, an assistant for a production manager.
Use only CALCULATED METRICS and RETRIEVED FACTORY RECORDS below.
If retrieved records are empty, answer only from calculated metrics and clearly
say when the available data is insufficient.

For arithmetic, ranking, target variance, downtime totals or comparisons,
prefer the calculated metrics.

QUESTION:
{question}

CALCULATED METRICS:
{calc}

RETRIEVED FACTORY RECORDS:
{retrieved or "No semantic records were available."}
"""

    return generate_text(
        st.session_state.client,
        prompt,
        max_output_tokens=1500,
    ), hits

def render_chat():
    st.markdown("## Ask the Factory")
    st.caption("Gemini 3.6 Flash with FAISS retrieval when the index is available.")

    if not st.session_state.data_ready:
        st.info("Upload and process some factory data first.")
        return

    if not st.session_state.generation_model_available:
        st.warning(
            "Gemini 3.6 Flash is not currently available to this API project/region. "
            "Use the dashboard for local analysis until it becomes available."
        )
        return

    if not st.session_state.rag_ready:
        st.info(
            "FAISS retrieval is not ready, so questions will use only the calculated "
            "factory summary. You can retry the FAISS index from Upload Data."
        )

    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED):
        with cols[i % 2]:
            if st.button(q, key=f"suggested_{i}", use_container_width=True):
                st.session_state["_pending_question"] = q

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    typed = st.chat_input(
        "Ask about targets, lines, supervisors, machines, downtime or issues…"
    )
    question = typed or st.session_state.pop("_pending_question", None)

    if not question:
        return

    st.session_state.chat_history.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analyzing factory records…"):
                answer, hits = answer_question(question)

            st.markdown(answer)

            if hits:
                with st.expander("Retrieved evidence"):
                    for h in hits[:6]:
                        st.caption(
                            f"{h['metadata'].get('source', 'Unknown')} • "
                            f"similarity {h['score']:.3f}"
                        )
                        st.write(h["text"])

            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )

        except GeminiModelUnavailableError as exc:
            mark_model_unavailable(str(exc))
            st.warning(str(exc))

        except GeminiTransientError:
            st.warning(
                "Gemini 3.6 Flash is temporarily busy after automatic retries. "
                "Your API key remains valid; try the question again shortly."
            )

        except Exception as exc:
            if is_auth_error(exc):
                invalidate_api_key(f"Gemini authentication failed: {exc}")
                st.rerun()
            st.error(f"Could not answer: {exc}")
