import streamlit as st

from src.gemini_client import (
    GENERATION_MODEL,
    validate_key,
    is_auth_error,
    is_transient_error,
)
from src.state import invalidate_api_key

def render_api_key_gate():
    st.markdown('<div class="login-spacer"></div>', unsafe_allow_html=True)
    _, center, _ = st.columns([1.2, 1.5, 1.2])

    with center:
        st.markdown(
            """
            <div class="key-card">
                <div class="key-icon">✦</div>
                <h1>FactoryOps AI</h1>
                <p>Connect Gemini to start your session-based production analysis.</p>
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

        st.caption(f"Generation: {GENERATION_MODEL} • Vector search: FAISS")

        if not submitted:
            return

        if not api_key.strip():
            st.warning("Enter a Gemini API key.")
            return

        with st.spinner("Validating API key…"):
            try:
                client, model_available, _ = validate_key(api_key.strip())

                st.session_state.api_key = api_key.strip()
                st.session_state.client = client
                st.session_state.api_key_valid = True
                st.session_state.auth_error = None
                st.session_state.generation_model_available = model_available

                if model_available:
                    st.session_state.model_warning = None
                else:
                    # Key is valid. Do not force the user back to the key screen.
                    st.session_state.model_warning = (
                        f"Your key is valid, but {GENERATION_MODEL} was not returned by "
                        "the Models API for this project/region. The dashboard can still "
                        "analyze uploaded data; Gemini-generated analysis will stay disabled "
                        "until the model becomes available."
                    )

                st.rerun()

            except Exception as exc:
                if is_auth_error(exc):
                    invalidate_api_key(
                        "The Gemini API key was rejected. Check the key and try again."
                    )
                    st.rerun()

                if is_transient_error(exc):
                    st.error(
                        "Gemini's API is temporarily unavailable. Your key was not marked "
                        "invalid. Try Connect Gemini again in a moment."
                    )
                else:
                    st.error(f"Could not validate the Gemini connection: {exc}")
