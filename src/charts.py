import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

def _valid(df, required):
    return (
        df is not None
        and isinstance(df, pd.DataFrame)
        and not df.empty
        and all(c in df.columns for c in required)
    )

def line_performance_chart(df):
    if not _valid(df, ["line_id", "achievement_pct"]):
        return None

    data = df.dropna(subset=["achievement_pct"]).copy()
    if data.empty:
        return None

    data = data.sort_values("achievement_pct", ascending=False)
    hover_cols = [
        c for c in ["target_units", "actual_units", "supervisor", "variance"]
        if c in data.columns
    ]

    fig = px.bar(
        data,
        x="line_id",
        y="achievement_pct",
        hover_data=hover_cols,
        labels={
            "line_id": "Production line",
            "achievement_pct": "Target achievement (%)",
        },
    )
    fig.add_hline(y=100, line_dash="dash", annotation_text="Target")
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def weekly_chart(df):
    if not _valid(df, ["week"]):
        return None

    fig = go.Figure()

    if "target_units" in df.columns and df["target_units"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["week"],
                y=df["target_units"],
                mode="lines+markers",
                name="Target",
            )
        )

    if "actual_units" in df.columns and df["actual_units"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["week"],
                y=df["actual_units"],
                mode="lines+markers",
                name="Actual",
            )
        )

    if not fig.data:
        return None

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def machine_downtime_chart(df):
    if not _valid(df, ["machine_id"]):
        return None

    if "downtime_minutes" in df.columns and df["downtime_minutes"].notna().any():
        metric = "downtime_minutes"
        label = "Downtime minutes"
    elif "issue_count" in df.columns and df["issue_count"].notna().any():
        metric = "issue_count"
        label = "Issue count"
    else:
        return None

    data = df.dropna(subset=[metric]).head(10).sort_values(metric)
    if data.empty:
        return None

    fig = px.bar(
        data,
        x=metric,
        y="machine_id",
        orientation="h",
        hover_data=[c for c in ["issue_count", "line_id"] if c in data.columns],
        labels={metric: label, "machine_id": "Machine"},
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def issue_chart(df):
    if not _valid(df, ["issue", "count"]):
        return None

    data = df.dropna(subset=["count"]).head(8).sort_values("count")
    if data.empty:
        return None

    fig = px.bar(
        data,
        x="count",
        y="issue",
        orientation="h",
        labels={"issue": "Issue type", "count": "Events"},
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
