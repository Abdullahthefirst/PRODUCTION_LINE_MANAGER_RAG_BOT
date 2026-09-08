import streamlit as st

from src.gemini_client import validate_key, is_auth_error
from src.state import invalidate_api_key

def render_api_key_gate():
    st.markdown('<div class="login-spacer"></div>', unsafe_allow_html=True)
    left, center, right = st.columns([1.2, 1.5, 1.2])
    with center:
        st.markdown(
            """
            <div class="key-card">
                <div class="key-icon">✦</div>
                <h1>FactoryOps AI</h1>
                <p>Connect Gemini to start your private, session-based production analysis.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)

        with st.form("api_key_form", clear_on_submit=False):
            api_key = st.text_input(
                "Gemini API key",
                type="password",
                placeholder="Paste your Gemini API key",
                help="The key is kept only in this Streamlit session state by this app.",
            )
            submitted = st.form_submit_button("Connect Gemini", use_container_width=True)

        st.caption("Model: Gemini 3.6 Flash • RAG index: FAISS (in memory)")

        if submitted:
            if not api_key.strip():
                st.warning("Enter a Gemini API key.")
                return
            with st.spinner("Validating key…"):
                try:
                    client, ok = validate_key(api_key.strip())
                    if not ok:
                        invalidate_api_key("Gemini did not return a validation response.")
                        st.rerun()
                    st.session_state.api_key = api_key.strip()
                    st.session_state.client = client
                    st.session_state.api_key_valid = True
                    st.session_state.auth_error = None
                    st.rerun()
                except Exception as exc:
    if is_auth_error(exc):
        invalidate_api_key(
            "The Gemini API key is invalid or does not have access."
        )
        st.rerun()

    # Key is not proven invalid.
    st.error(
        "Gemini is temporarily unavailable. "
        "Your API key was not rejected. Please try again."
    )
