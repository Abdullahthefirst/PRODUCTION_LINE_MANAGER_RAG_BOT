import json
import streamlit as st

from src.rag_engine import retrieve
from src.gemini_client import generate_text, is_auth_error
from src.state import invalidate_api_key

SUGGESTED = [
    "Which production line is furthest behind target?",
    "Which machine is causing the most downtime?",
    "What should the production manager prioritize this week?",
    "Are any machine issues recurring on underperforming lines?",
]

def _calculated_context():
    a = st.session_state.analysis
    line = a.get("line_summary")
    machine = a.get("machine_summary")
    return {
        "kpis": a.get("kpis", {}),
        "line_summary": [] if line is None or line.empty else line.head(20).to_dict(orient="records"),
        "machine_summary": [] if machine is None or machine.empty else machine.head(20).to_dict(orient="records"),
        "deterministic_findings": a.get("deterministic_findings", []),
    }

def answer_question(question):
    hits = retrieve(
        st.session_state.client,
        st.session_state.faiss_index,
        st.session_state.chunks,
        st.session_state.chunk_metadata,
        question,
        k=10,
    )
    retrieved = "\n\n".join(f"[{i+1}] {h['text']}" for i, h in enumerate(hits))
    calc = json.dumps(_calculated_context(), default=str)

    prompt = f"""
You are FactoryOps AI, an assistant for a production manager.
Use only CALCULATED METRICS and RETRIEVED FACTORY RECORDS below.
If the question asks for arithmetic, ranking, target variance, downtime totals, or comparison,
prefer the calculated metrics rather than guessing from retrieved text.
If evidence is insufficient, say exactly what information is missing.
Give a concise direct answer, then evidence, then an actionable suggestion when appropriate.

QUESTION:
{question}

CALCULATED METRICS:
{calc}

RETRIEVED FACTORY RECORDS:
{retrieved}
"""
    return generate_text(st.session_state.client, prompt, max_output_tokens=1500), hits

def render_chat():
    st.markdown("## Ask the Factory")
    st.caption("RAG assistant using Gemini 3.6 Flash + in-memory FAISS retrieval.")

    if not st.session_state.data_ready:
        st.info("Upload and process factory data first.")
        return

    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED):
        with cols[i % 2]:
            if st.button(q, key=f"suggested_{i}", use_container_width=True):
                st.session_state["_pending_question"] = q

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    typed = st.chat_input("Ask about targets, lines, supervisors, machines, downtime or issues…")
    question = typed or st.session_state.pop("_pending_question", None)

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing factory records…"):
                try:
                    answer, hits = answer_question(question)
                    st.markdown(answer)
                    with st.expander("Retrieved evidence"):
                        for h in hits[:6]:
                            st.caption(f"{h['metadata'].get('source','Unknown')} • similarity {h['score']:.3f}")
                            st.write(h["text"])
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    if is_auth_error(exc):
                        invalidate_api_key(f"Gemini authentication failed: {exc}")
                        st.rerun()
                    st.error(f"Could not answer: {exc}")
