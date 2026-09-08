import json
import streamlit as st

from src.gemini_client import generate_text, is_auth_error
from src.state import invalidate_api_key

def _compact_context(analysis, quality):
    line = analysis.get("line_summary")
    machine = analysis.get("machine_summary")
    issue = analysis.get("issue_summary")
    return {
        "kpis": analysis.get("kpis", {}),
        "line_summary": [] if line is None or line.empty else line.head(20).to_dict(orient="records"),
        "machine_summary": [] if machine is None or machine.empty else machine.head(20).to_dict(orient="records"),
        "issue_summary": [] if issue is None or issue.empty else issue.head(15).to_dict(orient="records"),
        "data_quality": quality,
        "calculated_findings": analysis.get("deterministic_findings", []),
    }

def generate_management_analysis():
    analysis = st.session_state.analysis
    quality = st.session_state.quality_report
    context = _compact_context(analysis, quality)
    prompt = f"""
You are a production-operations analyst for a mid-sized factory.
Analyze ONLY the supplied calculated factory data. Never invent missing facts.
Prioritize production target performance, recurring machine problems, downtime,
supervisor/line patterns, defect signals, risks, and next actions.

DATA:
{json.dumps(context, default=str)}

Return concise markdown with exactly these sections:
### Executive assessment
2-4 sentences.

### Priority findings
4-7 bullets, each grounded in supplied numbers when available.

### Recommended actions
4-6 practical management actions ordered by urgency.

### Data gaps affecting confidence
Mention only meaningful missing fields and how they limit analysis.
"""
    try:
        text = generate_text(st.session_state.client, prompt, max_output_tokens=1800)
        st.session_state.last_ai_analysis = text
        return text
    except Exception as exc:
        if is_auth_error(exc):
            invalidate_api_key(f"Gemini authentication failed: {exc}")
            st.rerun()
        raise
