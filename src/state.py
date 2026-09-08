import streamlit as st

def init_state():
    defaults = {
        "api_key": None,
        "api_key_valid": False,
        "client": None,
        "auth_error": None,
        "data_ready": False,
        "raw_tables": {},
        "raw_texts": [],
        "normalized": {},
        "quality_report": {},
        "analysis": {},
        "chunks": [],
        "faiss_index": None,
        "chunk_metadata": [],
        "chat_history": [],
        "last_ai_analysis": None,
        "file_summary": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_factory_data():
    for key, value in {
        "data_ready": False,
        "raw_tables": {},
        "raw_texts": [],
        "normalized": {},
        "quality_report": {},
        "analysis": {},
        "chunks": [],
        "faiss_index": None,
        "chunk_metadata": [],
        "chat_history": [],
        "last_ai_analysis": None,
        "file_summary": [],
    }.items():
        st.session_state[key] = value

def invalidate_api_key(message="The Gemini API key was rejected. Please enter a valid key."):
    st.session_state.api_key_valid = False
    st.session_state.api_key = None
    st.session_state.client = None
    st.session_state.auth_error = message
