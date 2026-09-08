import json
import streamlit as st

from src.gemini_client import generate_text

def _compact_context(analysis, quality):
    analysis = analysis or {}
    line = analysis.get("line_summary")
    machine = analysis.get("machine_summary")
    issue = analysis.get("issue_summary")

    return {
        "kpis": analysis.get("kpis", {}),
        "line_summary": (
            [] if line is None or line.empty
            else line.head(20).to_dict(orient="records")
        ),
        "machine_summary": (
            [] if machine is None or machine.empty
            else machine.head(20).to_dict(orient="records")
        ),
        "issue_summary": (
            [] if issue is None or issue.empty
            else issue.head(15).to_dict(orient="records")
        ),
        "data_quality": quality or {},
        "calculated_findings": analysis.get("deterministic_findings", []),
    }

def generate_management_analysis():
    context = _compact_context(
        st.session_state.analysis,
        st.session_state.quality_report,
    )

    prompt = f"""
You are a production-operations analyst for a mid-sized factory.
Analyze ONLY the supplied calculated factory data. Never invent missing facts.
If the dataset is incomplete, work with what exists and explicitly identify the gaps.

Prioritize:
- target vs actual performance
- production-line patterns
- recurring machine problems and downtime
- supervisor/line context
- defect signals
- operational risks
- practical next actions

DATA:
{json.dumps(context, default=str)}

Return concise markdown with exactly these sections:

### Executive assessment
2-4 sentences.

### Priority findings
Up to 7 bullets. Ground each in supplied evidence.

### Recommended actions
Up to 6 practical management actions ordered by urgency.

### Data gaps affecting confidence
Mention meaningful missing information and what analysis it prevents.
"""

    text = generate_text(
        st.session_state.client,
        prompt,
        max_output_tokens=1800,
    )
    st.session_state.last_ai_analysis = text
    return text
