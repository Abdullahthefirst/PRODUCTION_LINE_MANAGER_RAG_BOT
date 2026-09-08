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

# API key gate appears first and is removed from the UI after a successful validation.
# It is shown again only when an API call is classified as an authentication/key error.
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
        st.success("Factory data loaded", icon="✅")
        st.caption(f"{len(st.session_state.chunks)} searchable knowledge chunks")
        if st.button("Clear uploaded data", use_container_width=True):
            reset_factory_data()
            st.rerun()
    else:
        st.info("Upload factory data to begin.", icon="ℹ️")

    st.caption("Session-only: uploaded data and FAISS index are not persisted.")

if page == "Upload Data":
    render_upload_and_process()
elif page == "Ask Factory":
    render_chat()
else:
    render_dashboard()
