import streamlit as st

from src.state import init_state, reset_factory_data
from src.auth import render_api_key_gate
from src.styles import inject_css
from src.ingestion import render_upload_and_process
from src.dashboard import render_dashboard
from src.rag import render_chat

st.set_page_config(
    page_title="FactoryOps AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
inject_css()

# The key gate is the only intentional st.stop().
# Once a key is validated, it does NOT reappear for 503/high-demand/model errors.
# It reappears only when code explicitly calls invalidate_api_key() for a true auth failure.
if not st.session_state.api_key_valid:
    render_api_key_gate()
    st.stop()

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">F</div>
            <div>
                <div class="brand-name">FactoryOps</div>
                <div class="brand-sub">Production Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["Dashboard", "Upload Data", "Ask Factory"],
        label_visibility="collapsed",
    )

    st.divider()

    if st.session_state.data_ready:
        st.success("Factory files processed", icon="✅")
        st.caption(
            f"{len(st.session_state.chunks)} chunks • "
            f"{'FAISS ready' if st.session_state.rag_ready else 'FAISS not ready'}"
        )
        if st.button("Clear uploaded data", use_container_width=True):
            reset_factory_data()
            st.rerun()
    else:
        st.info("No factory files processed yet.", icon="ℹ️")

    if st.session_state.model_warning:
        st.warning("Gemini 3.6 Flash is currently unavailable for this API project/region.")

    st.caption("Session-only: uploaded data and FAISS index are not persisted.")

if page == "Upload Data":
    render_upload_and_process()
elif page == "Ask Factory":
    render_chat()
else:
    render_dashboard()
