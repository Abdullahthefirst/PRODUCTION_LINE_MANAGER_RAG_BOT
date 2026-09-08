import pandas as pd
import streamlit as st

from src.charts import (
    line_performance_chart,
    weekly_chart,
    machine_downtime_chart,
    issue_chart,
    PLOTLY_CONFIG,
)
from src.ai_analysis import generate_management_analysis
from src.gemini_client import (
    is_auth_error,
    GeminiTransientError,
    GeminiModelUnavailableError,
)
from src.state import invalidate_api_key, mark_model_unavailable

def _fmt_int(value):
    try:
        if value is None or pd.isna(value):
            return "—"
        return f"{float(value):,.0f}"
    except Exception:
        return "—"

def _has_df(value):
    return isinstance(value, pd.DataFrame) and not value.empty

def _empty_dashboard():
    st.markdown(
        """
        <div class="hero">
            <h2>Production Control Center</h2>
            <p>Upload whatever production data you currently have. Missing targets,
            machine logs, supervisors or weekly fields will be shown as data gaps rather
            than stopping the dashboard.</p>
            <span class="hero-chip">Gemini 3.6 Flash • FAISS • Session-only</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planned output", "—")
    c2.metric("Actual output", "—")
    c3.metric("Target achievement", "—")
    c4.metric("Logged downtime", "—")

    left, right = st.columns([1.5, 1])
    with left:
        st.info("Upload files from **Upload Data** to populate production charts.")
    with right:
        st.markdown("### What the app can detect")
        st.write("• quarter and weekly targets")
        st.write("• line and supervisor performance")
        st.write("• machine issues and recurring downtime")
        st.write("• missing information and confidence gaps")
    return

def render_dashboard():
    if not st.session_state.data_ready:
        _empty_dashboard()
        return

    a = st.session_state.analysis or {}
    k = a.get("kpis", {}) or {}
    q = st.session_state.quality_report or {}

    st.markdown(
        f"""
        <div class="hero">
            <h2>Production Control Center</h2>
            <p>Analysis of the factory files loaded in this session.</p>
            <span class="hero-chip">
                Data readiness {q.get('score', 0)}% •
                {q.get('row_count', 0)} rows •
                {len(st.session_state.chunks)} searchable chunks
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.model_warning:
        st.warning(st.session_state.model_warning)

    if st.session_state.embedding_error:
        st.info(
            "Dashboard analytics are available even though semantic RAG indexing is not currently ready."
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planned output", _fmt_int(k.get("total_target")))
    c2.metric(
        "Actual output",
        _fmt_int(k.get("total_actual")),
        delta=_fmt_int(k.get("variance")) if "variance" in k else None,
    )
    c3.metric(
        "Target achievement",
        f"{float(k.get('achievement_pct', 0)):.1f}%"
        if "achievement_pct" in k and k.get("total_target", 0)
        else "—",
    )
    c4.metric(
        "Logged downtime",
        f"{float(k.get('downtime_hours', 0)):,.1f} h"
        if "downtime_hours" in k
        else "—",
    )

    line_df = a.get("line_summary")
    weekly_df = a.get("weekly_summary")
    machine_df = a.get("machine_summary")
    issue_df = a.get("issue_summary")

    # Optional interactive line filter. It never assumes line data exists.
    selected_line = "All lines"
    if _has_df(line_df) and "line_id" in line_df.columns:
        options = ["All lines"] + sorted(
            line_df["line_id"].dropna().astype(str).unique().tolist()
        )
        selected_line = st.selectbox("Production line view", options)

    left, right = st.columns([1.6, 1])

    with left:
        st.markdown("### Weekly production")
        fig = weekly_chart(weekly_df)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info(
                "Weekly trend is unavailable because the uploaded data does not contain "
                "a usable week plus target/actual combination."
            )

    with right:
        st.markdown("### Data readiness")
        checks = q.get("checks", {})
        if checks:
            for label, ok in checks.items():
                st.write(("✅ " if ok else "⚠️ ") + label)
        else:
            st.info("No recognizable factory fields were detected yet.")

        if q.get("missing"):
            st.caption(
                "Missing fields reduce the scope of analysis, but do not stop the dashboard."
            )

    left, right = st.columns(2)

    with left:
        st.markdown("### Line performance")
        display_line = line_df

        if (
            _has_df(line_df)
            and selected_line != "All lines"
            and "line_id" in line_df.columns
        ):
            display_line = line_df[
                line_df["line_id"].astype(str) == selected_line
            ]

        fig = line_performance_chart(display_line)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        if _has_df(display_line):
            cols = [
                c for c in [
                    "line_id",
                    "supervisor",
                    "target_units",
                    "actual_units",
                    "achievement_pct",
                    "variance",
                    "downtime_hours",
                    "defect_units",
                ]
                if c in display_line.columns
            ]
            if cols:
                st.dataframe(
                    display_line[cols],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Line records exist, but no standard performance columns were detected.")
        elif fig is None:
            st.info("Line-level performance could not be calculated from the current files.")

    with right:
        st.markdown("### Machine impact")
        display_machine = machine_df

        if (
            _has_df(machine_df)
            and selected_line != "All lines"
            and "line_id" in machine_df.columns
        ):
            display_machine = machine_df[
                machine_df["line_id"].astype(str) == selected_line
            ]

        fig = machine_downtime_chart(display_machine)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        if _has_df(display_machine):
            st.dataframe(
                display_machine.head(12),
                use_container_width=True,
                hide_index=True,
            )
        elif fig is None:
            st.info("No machine issue/downtime data is available for this view.")

    left, right = st.columns(2)

    with left:
        st.markdown("### Frequent machine issues")
        fig = issue_chart(issue_df)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("No usable issue descriptions were detected.")

    with right:
        st.markdown("### Calculated alerts")
        findings = a.get("deterministic_findings", [])
        if findings:
            for item in findings:
                st.warning(item, icon="⚠️")
        else:
            st.info(
                "No alerts could be calculated. This can simply mean the uploaded data "
                "does not yet contain enough comparable fields."
            )

    with st.expander("Uploaded data preview"):
        tables = st.session_state.normalized or {}
        if not tables:
            st.info("No tabular records were extracted.")
        else:
            for name, df in list(tables.items())[:8]:
                st.markdown(f"**{name}**")
                if df is None or df.empty:
                    st.caption("Empty table")
                else:
                    st.dataframe(df.head(15), use_container_width=True, hide_index=True)

    st.markdown("### AI management analysis")

    if not st.session_state.generation_model_available:
        st.warning(
            "Gemini 3.6 Flash is not currently available to this API project/region. "
            "The deterministic dashboard remains fully usable."
        )
        return

    run = st.button(
        "Generate / refresh analysis",
        type="primary",
        use_container_width=False,
    )

    if run:
        try:
            with st.spinner("Gemini 3.6 Flash is preparing management insights…"):
                text = generate_management_analysis()
                st.markdown(text)

        except GeminiModelUnavailableError as exc:
            mark_model_unavailable(str(exc))
            st.warning(str(exc))

        except GeminiTransientError:
            st.warning(
                "Gemini 3.6 Flash is temporarily under high demand. The app retried "
                "automatically; try the analysis again shortly. Your API key remains accepted."
            )

        except Exception as exc:
            if is_auth_error(exc):
                invalidate_api_key(f"Gemini authentication failed: {exc}")
                st.rerun()
            st.error(f"AI analysis failed: {exc}")

    elif st.session_state.last_ai_analysis:
        st.markdown(st.session_state.last_ai_analysis)
    else:
        st.info(
            "The charts and alerts above are calculated locally. Generate an AI assessment "
            "when you want a management summary and recommended actions."
        )
