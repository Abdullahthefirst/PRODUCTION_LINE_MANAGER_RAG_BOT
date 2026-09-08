import plotly.express as px
import plotly.graph_objects as go

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

def line_performance_chart(df):
    if df is None or df.empty:
        return None
    data = df.sort_values("achievement_pct", ascending=False)
    fig = px.bar(
        data,
        x="line_id",
        y="achievement_pct",
        hover_data=[c for c in ["target_units", "actual_units", "supervisor", "variance"] if c in data.columns],
        labels={"line_id": "Production line", "achievement_pct": "Target achievement (%)"},
    )
    fig.add_hline(y=100, line_dash="dash", annotation_text="Target")
    fig.update_layout(height=330, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def weekly_chart(df):
    if df is None or df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["week"], y=df["target_units"], mode="lines+markers", name="Target"))
    fig.add_trace(go.Scatter(x=df["week"], y=df["actual_units"], mode="lines+markers", name="Actual"))
    fig.update_layout(height=330, margin=dict(l=10,r=10,t=25,b=10), legend=dict(orientation="h"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def machine_downtime_chart(df):
    if df is None or df.empty:
        return None
    y = "downtime_minutes" if "downtime_minutes" in df.columns else "issue_count"
    data = df.head(10).sort_values(y)
    fig = px.bar(data, x=y, y="machine_id", orientation="h",
                 hover_data=[c for c in ["issue_count", "line_id"] if c in data.columns],
                 labels={y: "Downtime minutes" if y == "downtime_minutes" else "Issue count", "machine_id": "Machine"})
    fig.update_layout(height=330, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def issue_chart(df):
    if df is None or df.empty:
        return None
    data = df.head(8).sort_values("count")
    fig = px.bar(data, x="count", y="issue", orientation="h", labels={"issue":"Issue type","count":"Events"})
    fig.update_layout(height=330, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
