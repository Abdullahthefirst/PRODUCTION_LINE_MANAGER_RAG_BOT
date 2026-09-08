import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --navy: #263957;
            --ink: #172033;
            --muted: #6f7b91;
            --panel: #ffffff;
            --soft: #f4f7fb;
            --line: #e7ebf2;
            --violet: #5b5ce2;
            --blue: #1686e8;
        }
        .stApp { background: #f3f6fb; }
        .block-container { padding-top: 1.3rem; padding-bottom: 2rem; max-width: 1500px; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e7ebf2; }
        [data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
        .brand { display:flex; gap:.7rem; align-items:center; margin:.1rem 0 1.2rem 0; }
        .brand-mark { width:38px; height:38px; border-radius:12px; display:grid; place-items:center;
                      color:white; font-weight:800; background:linear-gradient(135deg,#5b5ce2,#1389e9); }
        .brand-name { font-weight:800; font-size:1.05rem; color:#1c2940; }
        .brand-sub { color:#8993a5; font-size:.72rem; }
        .hero {
            border-radius:20px; padding:1.35rem 1.55rem; color:white;
            background:linear-gradient(115deg,#234f9c 0%,#5a50d5 60%,#6136c7 100%);
            min-height:145px; margin-bottom:.8rem;
        }
        .hero h2 { margin:0 0 .25rem 0; font-size:1.45rem; }
        .hero p { margin:.2rem 0; opacity:.88; }
        .hero-chip {display:inline-block; margin-top:.8rem; background:rgba(255,255,255,.16);
                    padding:.34rem .62rem; border-radius:99px; font-size:.78rem;}
        .kpi-card, .panel {
            background:#fff; border:1px solid #e7ebf2; border-radius:18px;
        }
        .kpi-card { padding:1rem 1.05rem; min-height:116px; }
        .kpi-label { color:#6e788b; font-size:.77rem; font-weight:600; }
        .kpi-value { color:#1c2940; font-size:1.7rem; font-weight:800; margin:.2rem 0; }
        .kpi-sub { color:#8c96a7; font-size:.72rem; }
        .panel { padding:1rem 1.05rem; margin:.25rem 0 .8rem 0; }
        .panel-title {font-weight:800; color:#1e2a40; margin-bottom:.65rem;}
        .status-good {color:#17884e; font-weight:700;}
        .status-warn {color:#b66b00; font-weight:700;}
        .status-bad {color:#c13f4a; font-weight:700;}
        .readiness-row {display:flex; justify-content:space-between; gap:1rem; padding:.44rem 0;
                        border-bottom:1px solid #eef1f6; font-size:.84rem;}
        .login-spacer { height: 4rem; }
        .key-card {
            text-align:center; background:#fff; border:1px solid #e7ebf2; border-radius:22px;
            padding:1.5rem 1.2rem 1rem 1.2rem; margin-bottom:.8rem;
        }
        .key-icon {width:52px;height:52px;margin:0 auto .7rem auto;border-radius:16px;display:grid;
                   place-items:center;color:#fff;font-size:1.4rem;background:linear-gradient(135deg,#5b5ce2,#1389e9);}
        .key-card h1 {font-size:1.45rem;margin:.15rem 0;}
        .key-card p {color:#727f94;margin:.25rem 0;}
        div[data-testid="stMetric"] { background:#fff; border:1px solid #e7ebf2; border-radius:16px; padding:14px; }
        .stButton > button { border-radius:11px; }
        .stFileUploader { background:#fff; border-radius:16px; padding:.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
