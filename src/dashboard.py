import streamlit as st

from src.charts import (
    line_performance_chart, weekly_chart, machine_downtime_chart, issue_chart, PLOTLY_CONFIG
)
from src.ai_analysis import generate_management_analysis
from src.gemini_client import is_auth_error
from src.state import invalidate_api_key

def _fmt_int(v):
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "—"

def render_dashboard():
    if not st.session_state.data_ready:
        st.markdown(
            """
            <div class="hero">
                <h2>Production intelligence, without a database</h2>
                <p>Upload your current factory files, normalize them, detect missing information,
                calculate performance, identify recurring machine issues, and query everything through RAG.</p>
                <span class="hero-chip">Session-only • Gemini 3.6 Flash • FAISS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Open **Upload Data** from the sidebar to begin.")
        return

    a = st.session_state.analysis
    k = a.get("kpis", {})
    q = st.session_state.quality_report

    st.markdown(
        f"""
        <div class="hero">
            <h2>Production Control Center</h2>
            <p>Live analysis of the files loaded in this session.</p>
            <span class="hero-chip">Data readiness {q.get('score', 0)}% • {len(st.session_state.chunks)} indexed chunks</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planned output", _fmt_int(k.get("total_target")))
    c2.metric("Actual output", _fmt_int(k.get("total_actual")), delta=_fmt_int(k.get("variance", 0)))
    c3.metric("Target achievement", f"{k.get('achievement_pct',0):.1f}%")
    c4.metric("Logged downtime", f"{k.get('downtime_hours',0):,.1f} h" if "downtime_hours" in k else "—")

    left, right = st.columns([1.6, 1])
    with left:
        st.markdown("### Production performance")
        fig = weekly_chart(a.get("weekly_summary"))
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("Weekly fields were not detected.")

    with right:
        st.markdown("### Data readiness")
        for label, ok in q.get("checks", {}).items():
            st.markdown(f"{'✅' if ok else '⚠️'} {label}")
        if q.get("missing"):
            st.caption("Missing fields reduce the confidence of some analyses.")

    left, right = st.columns(2)
    with left:
        st.markdown("### Line target achievement")
        fig = line_performance_chart(a.get("line_summary"))
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
            show = a["line_summary"].copy()
            cols = [c for c in ["line_id","supervisor","target_units","actual_units","achievement_pct","variance"] if c in show.columns]
            st.dataframe(show[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Line target/actual fields were not detected.")

    with right:
        st.markdown("### Machine downtime / issue impact")
        fig = machine_downtime_chart(a.get("machine_summary"))
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
            show = a["machine_summary"].head(10)
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.info("Machine issue fields were not detected.")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Frequent machine issues")
        fig = issue_chart(a.get("issue_summary"))
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("Issue descriptions were not detected.")

    with right:
        st.markdown("### Calculated alerts")
        findings = a.get("deterministic_findings", [])
        if findings:
            for item in findings:
                st.warning(item, icon="⚠️")
        else:
            st.info("No deterministic alerts could be calculated from the supplied columns.")

    st.markdown("### AI management analysis")
    b1, b2 = st.columns([1, 3])
    with b1:
        run = st.button("Generate / refresh analysis", type="primary", use_container_width=True)
    with b2:
        st.caption("Gemini receives calculated summaries and data-quality information, not a hidden database.")

    if run:
        try:
            with st.spinner("Gemini is preparing management insights…"):
                text = generate_management_analysis()
                st.markdown(text)
        except Exception as exc:
            if is_auth_error(exc):
                invalidate_api_key(f"Gemini authentication failed: {exc}")
                st.rerun()
            st.error(f"AI analysis failed: {exc}")
    elif st.session_state.last_ai_analysis:
        st.markdown(st.session_state.last_ai_analysis)
    else:
        st.info("Generate an AI assessment when you want a management summary and suggested actions.")
