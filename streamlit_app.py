import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentryScreen | Adverse Media Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & Root ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #020817 !important;
    color: #e2e8f0 !important;
}

/* ── Radial gradient background ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.06) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 10%, rgba(6,182,212,0.04) 0%, transparent 50%);
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
    border-right: 1px solid rgba(51,65,85,0.6) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: #e2e8f0 !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    color: #a5b4fc !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.3) !important;
    border-color: rgba(99,102,241,0.6) !important;
}

/* ── Main layout ── */
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

/* ── Header ── */
.ss-header {
    text-align: center;
    margin-bottom: 2.5rem;
    animation: fadeIn 0.6s ease-out;
}
.ss-header .icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 72px; height: 72px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px;
    margin-bottom: 1rem;
    font-size: 2rem;
}
.ss-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #f1f5f9;
    margin: 0 0 0.5rem 0;
    line-height: 1.15;
}
.ss-header .gradient-text {
    background: linear-gradient(135deg, #818cf8 0%, #22d3ee 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.ss-header p {
    color: #64748b;
    font-size: 1rem;
    margin: 0;
}

/* ── Glass card ── */
.glass-card {
    background: rgba(15, 23, 42, 0.70);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(51,65,85,0.6);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    animation: slideUp 0.4s ease-out;
}
.glass-card h3 {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    margin: 0 0 1rem 0;
}

/* ── Risk Banner ── */
.risk-banner {
    background: rgba(15, 23, 42, 0.70);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(51,65,85,0.6);
    border-radius: 20px;
    padding: 1.25rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.25rem;
    animation: fadeIn 0.4s ease-out;
}
.risk-banner .entity-info span {
    display: block;
    font-size: 0.85rem;
    color: #64748b;
}
.risk-banner .entity-info strong { color: #e2e8f0; }
.risk-banner .entity-info .resolved { color: #a5b4fc; font-weight: 600; }
.alias-tag {
    display: inline-block;
    background: rgba(30,41,59,0.9);
    border: 1px solid rgba(71,85,105,0.5);
    color: #94a3b8;
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 999px;
    margin: 2px;
}

/* ── Metric Cards ── */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.25rem;
}
@media (max-width: 768px) { .metrics-row { grid-template-columns: repeat(2, 1fr); } }
.metric-tile {
    background: rgba(15, 23, 42, 0.70);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(51,65,85,0.5);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    animation: slideUp 0.4s ease-out;
}
.metric-tile::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
}
.metric-tile.indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }
.metric-tile.cyan::before   { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
.metric-tile.amber::before  { background: linear-gradient(90deg, #f59e0b, #fcd34d); }
.metric-tile.slate::before  { background: linear-gradient(90deg, #475569, #64748b); }
.metric-tile label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #64748b;
    display: block;
    margin-bottom: 0.4rem;
}
.metric-tile .value {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-tile .sub {
    font-size: 0.78rem;
    color: #94a3b8;
}

/* ── Risk Score Gauge ── */
.risk-gauge-wrap {
    background: rgba(15, 23, 42, 0.70);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(51,65,85,0.6);
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    animation: slideUp 0.4s ease-out;
}
.risk-arc {
    position: relative;
    display: inline-block;
    width: 180px;
    height: 95px;
    margin: 1rem auto;
}
.gauge-label-center {
    font-size: 2.2rem;
    font-weight: 800;
    color: #f1f5f9;
    margin: 0.5rem 0 0.2rem;
}
.gauge-cat {
    display: inline-block;
    padding: 3px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.cat-HIGH     { background: rgba(239,68,68,0.15);   color: #f87171; border: 1px solid rgba(239,68,68,0.35); }
.cat-MEDIUM   { background: rgba(245,158,11,0.15);  color: #fbbf24; border: 1px solid rgba(245,158,11,0.35); }
.cat-LOW      { background: rgba(16,185,129,0.15);  color: #34d399; border: 1px solid rgba(16,185,129,0.35); }

/* ── Severity Badges ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-CRITICAL { background: rgba(190,18,60,0.2);  color: #fb7185; border: 1px solid rgba(190,18,60,0.4); }
.badge-HIGH     { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.35); }
.badge-MEDIUM   { background: rgba(245,158,11,0.15);color: #fbbf24; border: 1px solid rgba(245,158,11,0.35); }
.badge-LOW      { background: rgba(16,185,129,0.15);color: #34d399; border: 1px solid rgba(16,185,129,0.35); }

/* ── Summary Box ── */
.summary-box {
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    color: #c7d2fe;
    font-size: 0.9rem;
    line-height: 1.65;
    margin-bottom: 1rem;
}

/* ── Keywords ── */
.kw-tag {
    display: inline-block;
    background: rgba(245,158,11,0.15);
    border: 1px solid rgba(245,158,11,0.3);
    color: #fcd34d;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 999px;
    margin: 3px 3px 3px 0;
}

/* ── Risk Factor ── */
.risk-factor {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(51,65,85,0.35);
    font-size: 0.85rem;
    color: #94a3b8;
}
.risk-factor:last-child { border-bottom: none; }
.risk-factor::before {
    content: '▸';
    color: #f87171;
    flex-shrink: 0;
    margin-top: 2px;
}

/* ── Article Card ── */
.article-card {
    background: rgba(30,41,59,0.5);
    border: 1px solid rgba(51,65,85,0.5);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, transform 0.2s;
    cursor: pointer;
}
.article-card:hover {
    border-color: rgba(99,102,241,0.4);
    transform: translateY(-1px);
}
.article-card .art-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.3rem;
}
.article-card .art-meta {
    font-size: 0.75rem;
    color: #64748b;
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}
.article-card .art-meta span { display: flex; align-items: center; gap: 3px; }
.article-card .why-flagged {
    font-size: 0.8rem;
    color: #a5b4fc;
    background: rgba(99,102,241,0.08);
    border-left: 3px solid rgba(99,102,241,0.5);
    padding: 0.4rem 0.6rem;
    border-radius: 0 8px 8px 0;
    margin-top: 0.5rem;
}

/* ── Review Buttons ── */
.review-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.6rem 1.25rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid;
    transition: all 0.2s;
    width: 100%;
}

/* ── Input overrides ── */
.stTextInput > div > div > input {
    background: rgba(30,41,59,0.7) !important;
    border: 1px solid rgba(71,85,105,0.6) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(99,102,241,0.7) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #475569 !important; }

/* ── Primary button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 2rem !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
    transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4338ca, #4f46e5) !important;
    box-shadow: 0 6px 24px rgba(99,102,241,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Checkbox ── */
.stCheckbox > label {
    color: #94a3b8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}

/* ── Divider ── */
hr { border-color: rgba(51,65,85,0.4) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(51,65,85,0.5) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── Success / Info / Warning / Error ── */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Animations ── */
@keyframes fadeIn  { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* ── Expander ── */
details {
    background: rgba(30,41,59,0.5) !important;
    border: 1px solid rgba(51,65,85,0.5) !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden !important;
}
details summary {
    padding: 0.75rem 1rem !important;
    cursor: pointer !important;
    color: #cbd5e1 !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
}
details summary:hover { background: rgba(51,65,85,0.3) !important; }
details[open] summary { border-bottom: 1px solid rgba(51,65,85,0.5) !important; }

/* ── Section Headers ── */
.section-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(51,65,85,0.3);
}

/* ── Live news badge ── */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    color: #f87171;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 999px;
    letter-spacing: 0.05em;
    vertical-align: middle;
}
.live-dot {
    width: 6px; height: 6px;
    background: #f87171;
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.75); }
}

/* ── Stmetric overrides ── */
[data-testid="metric-container"] {
    background: rgba(15,23,42,0.7) !important;
    border: 1px solid rgba(51,65,85,0.5) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"]  { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
[data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.85rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api"


def risk_color_class(cat: str) -> str:
    return {"HIGH": "cat-HIGH", "MEDIUM": "cat-MEDIUM", "LOW": "cat-LOW"}.get(cat, "cat-LOW")


def severity_badge(sev: str) -> str:
    s = sev.upper()
    return f'<span class="badge badge-{s}">{s}</span>'


def score_bar(score: float, max_score: float = 1.0) -> str:
    pct = min(100, int(score / max_score * 100))
    color = "#f87171" if pct > 65 else "#fbbf24" if pct > 35 else "#34d399"
    return (
        f'<div style="background:rgba(51,65,85,0.4);border-radius:999px;height:6px;overflow:hidden;margin-top:4px;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:999px;transition:width 0.8s ease;"></div>'
        f'</div>'
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.2rem;margin-bottom:0.4rem;">🛡️</div>
        <div style="font-size:1.2rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.02em;">SentryScreen</div>
        <div style="font-size:0.8rem;color:#64748b;margin-top:2px;">Adverse Media Copilot</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="margin:0.75rem 0 1rem;">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)

    if st.button("🔄  Refresh Backend Status", use_container_width=True):
        try:
            health = requests.get(f"{API_BASE}/health", timeout=5).json()
            stats = requests.get(f"{API_BASE}/dataset-stats", timeout=5).json()
            st.success("✓ Backend Connected")
            st.markdown(f"""
            <div style="font-size:0.82rem;color:#94a3b8;line-height:1.8;margin-top:0.5rem;">
                <div>🖥️ <b style="color:#cbd5e1;">Device:</b> {health.get('device','?').upper()}</div>
                <div>⚡ <b style="color:#cbd5e1;">Hardware:</b> {health.get('device_name','?')}</div>
                <div>📰 <b style="color:#cbd5e1;">Articles:</b> {stats.get('total_articles','?'):,}</div>
                <div>🏢 <b style="color:#cbd5e1;">Entities:</b> {stats.get('unique_entities','?')}</div>
                <div>📦 <b style="color:#cbd5e1;">Version:</b> {health.get('version','?')}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("⚠️ Backend Offline")
            st.markdown(
                '<div style="font-size:0.78rem;color:#64748b;margin-top:0.4rem;">Ensure FastAPI is running on port 8000.</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr style="margin:1rem 0;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quick Reference</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.78rem;color:#475569;line-height:2;">
        <div>🔴 <b style="color:#94a3b8;">HIGH</b> — Score > 70</div>
        <div>🟡 <b style="color:#94a3b8;">MEDIUM</b> — Score 30–70</div>
        <div>🟢 <b style="color:#94a3b8;">LOW</b> — Score < 30</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="margin:1rem 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.72rem;color:#334155;text-align:center;padding-bottom:0.5rem;">
        Powered by AMD ROCm · FAISS · SentenceTransformers
    </div>
    """, unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ss-header">
    <div class="icon-wrap">🛡️</div>
    <h1>Adverse Media <span class="gradient-text">Copilot</span></h1>
    <p>AI-powered entity screening with vector similarity search and explainable risk scoring.</p>
</div>
""", unsafe_allow_html=True)

# ── Search Bar ───────────────────────────────────────────────────────────────
col_inp, col_btn = st.columns([5, 1])
with col_inp:
    query = st.text_input(
        label="entity_search",
        label_visibility="collapsed",
        placeholder="🔍  Enter company or person name — e.g. Nexum Capital Partners",
        key="search_query",
    )

with col_btn:
    search_clicked = st.button("Screen ➜", type="primary", use_container_width=True)

col_chk1, col_chk2, _ = st.columns([2, 2, 3])
with col_chk1:
    use_live_web = st.checkbox(
        "🌐  Fetch Recent News (Live Web)",
        help="Searches DuckDuckGo in real-time for adverse news articles about the entity.",
    )
with col_chk2:
    show_article_text = st.checkbox("📄  Show Full Article Text", value=False)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Screening Logic ───────────────────────────────────────────────────────────
if search_clicked and query.strip():
    mode_label = (
        '<span class="live-badge"><span class="live-dot"></span>LIVE NEWS</span>'
        if use_live_web
        else '<span style="font-size:0.8rem;color:#64748b;">Dataset search</span>'
    )

    spinner_msg = (
        f"Fetching recent news for **{query}** and running analysis…"
        if use_live_web
        else f"Screening **{query}** across the adverse media database…"
    )

    with st.spinner(spinner_msg):
        try:
            res = requests.post(
                f"{API_BASE}/screen",
                json={
                    "entity_name": query.strip(),
                    "top_k": 10,
                    "threshold": 0.15,
                    "use_live_web": use_live_web,
                },
                timeout=90,
            )

            if res.status_code == 200:
                data = res.json()
                risk_cat = data["risk_category"]
                risk_score = data["risk_score"]
                confidence = data["confidence_score"]

                # ── Resolution Banner ──────────────────────────────────────
                aliases_html = "".join(
                    f'<span class="alias-tag">{a}</span>'
                    for a in (data["entity"].get("aliases") or [])
                )
                st.markdown(f"""
                <div class="risk-banner">
                    <div class="entity-info">
                        <span>Queried: <strong>{data['entity']['original_name']}</strong> {mode_label}</span>
                        <span>Resolved to: <span class="resolved">{data['entity']['resolved_name']}</span>
                              &nbsp;·&nbsp; Confidence: {data['entity']['confidence']*100:.1f}%</span>
                    </div>
                    <div>{aliases_html}</div>
                </div>
                """, unsafe_allow_html=True)

                # ── Metric Tiles ───────────────────────────────────────────
                c1, c2, c3, c4 = st.columns(4)
                cat_emoji = "🔴" if risk_cat == "HIGH" else "🟡" if risk_cat == "MEDIUM" else "🟢"
                c1.metric("Risk Score", f"{risk_score:.1f} / 100", f"{cat_emoji} {risk_cat}", delta_color="off")
                c2.metric("Confidence", f"{confidence*100:.1f}%")
                c3.metric("Articles Flagged", data["total_articles_found"])
                c4.metric("Processing Time", f"{data.get('processing_time_ms', 0):.0f} ms")

                st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

                # ── Main Grid: Gauge + Explainability ─────────────────────
                gauge_col, exp_col = st.columns([4, 8])

                with gauge_col:
                    # SVG arc gauge
                    pct = risk_score / 100
                    arc_angle = pct * 180  # 0° = left, 180° = right
                    import math
                    theta = math.radians(180 - arc_angle)
                    cx, cy, r = 90, 90, 70
                    end_x = cx + r * math.cos(theta)
                    end_y = cy - r * math.sin(theta)
                    gauge_color = "#f87171" if risk_cat == "HIGH" else "#fbbf24" if risk_cat == "MEDIUM" else "#34d399"

                    st.markdown(f"""
                    <div class="glass-card" style="text-align:center;">
                        <div class="section-title" style="text-align:left;">Risk Score</div>
                        <svg viewBox="0 0 180 110" width="100%" style="max-width:220px;margin:0 auto;display:block;">
                            <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="rgba(51,65,85,0.6)" stroke-width="10" stroke-linecap="round"/>
                            <path d="M 20 90 A 70 70 0 0 1 {end_x:.2f} {end_y:.2f}"
                                  fill="none" stroke="{gauge_color}" stroke-width="10" stroke-linecap="round"
                                  style="filter:drop-shadow(0 0 6px {gauge_color}88)"/>
                            <text x="90" y="80" text-anchor="middle" font-size="26" font-weight="800" fill="#f1f5f9" font-family="Inter,sans-serif">{risk_score:.0f}</text>
                            <text x="90" y="100" text-anchor="middle" font-size="10" fill="#64748b" font-family="Inter,sans-serif">out of 100</text>
                        </svg>
                        <div class="gauge-cat {risk_color_class(risk_cat)}" style="margin:0.25rem auto 0.75rem;">{risk_cat} RISK</div>

                        <div style="text-align:left;">
                            <div class="section-title" style="margin-bottom:0.5rem;">Risk Breakdown</div>
                    """, unsafe_allow_html=True)

                    breakdown = data.get("risk_breakdown", {})
                    breakdown_labels = {
                        "relevance_contribution": ("Relevance", "#818cf8"),
                        "severity_contribution":  ("Severity",  "#f87171"),
                        "frequency_contribution": ("Frequency", "#fbbf24"),
                        "recency_contribution":   ("Recency",   "#34d399"),
                    }
                    for key, (label, color) in breakdown_labels.items():
                        val = breakdown.get(key, 0) * 100
                        st.markdown(f"""
                        <div style="margin-bottom:0.5rem;">
                            <div style="display:flex;justify-content:space-between;font-size:0.77rem;color:#94a3b8;margin-bottom:3px;">
                                <span>{label}</span><span style="color:{color};font-weight:600;">{val:.1f}</span>
                            </div>
                            <div style="background:rgba(51,65,85,0.4);border-radius:999px;height:5px;overflow:hidden;">
                                <div style="width:{min(val,100):.1f}%;height:100%;background:{color};border-radius:999px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div></div>", unsafe_allow_html=True)

                with exp_col:
                    expl = data.get("explainability", {})
                    st.markdown("""
                    <div class="glass-card">
                        <div class="section-title">Executive Summary</div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="summary-box">{expl.get("summary","No summary available.")}</div>', unsafe_allow_html=True)

                    kw_html = " ".join(f'<span class="kw-tag">{kw}</span>' for kw in expl.get("top_keywords", []))
                    st.markdown(f"""
                    <div style="margin-bottom:0.75rem;">
                        <div style="font-size:0.75rem;font-weight:600;color:#475569;letter-spacing:0.07em;text-transform:uppercase;margin-bottom:0.5rem;">Top Keywords</div>
                        <div>{kw_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    risk_factors = expl.get("key_risk_factors", [])
                    if risk_factors:
                        st.markdown("""
                        <div>
                            <div style="font-size:0.75rem;font-weight:600;color:#475569;letter-spacing:0.07em;text-transform:uppercase;margin-bottom:0.5rem;">Key Risk Factors</div>
                        """, unsafe_allow_html=True)
                        for factor in risk_factors:
                            st.markdown(f'<div class="risk-factor">{factor}</div>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

                # ── Articles ───────────────────────────────────────────────
                articles = data.get("articles", [])
                st.markdown(f"""
                <div class="glass-card">
                    <div class="section-title">
                        Adverse Media Findings
                        <span style="float:right;font-size:0.8rem;color:#94a3b8;font-weight:500;letter-spacing:0;text-transform:none;">
                            {len(articles)} article(s) found
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                if articles:
                    for i, art in enumerate(articles):
                        sev = art.get("severity_label", "LOW").upper()
                        rel_score = art.get("relevance_score", 0)
                        source_display = art.get("source", "Unknown")
                        if source_display.startswith("http"):
                            source_display = source_display.split("/")[2] if len(source_display.split("/")) > 2 else source_display

                        date_str = art.get("published_date", "")[:10] or "Unknown date"
                        title = art.get("article_title", "Untitled")
                        why = art.get("why_flagged", "")
                        body = art.get("article_text", "")
                        category = art.get("category", "")

                        bar_html = score_bar(rel_score)
                        badge_html = severity_badge(sev)
                        category_tag = (
                            f'<span style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);'
                            f'color:#a5b4fc;font-size:0.7rem;padding:2px 8px;border-radius:999px;">{category}</span>'
                            if category else ""
                        )

                        with st.expander(f"  {title}", expanded=False):
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.75rem;">
                                {badge_html}
                                {category_tag}
                                <span style="font-size:0.75rem;color:#64748b;">📅 {date_str}</span>
                                <span style="font-size:0.75rem;color:#64748b;">🔗 {source_display}</span>
                                <span style="font-size:0.75rem;color:#94a3b8;margin-left:auto;">Relevance: <b style="color:#e2e8f0;">{rel_score:.3f}</b></span>
                            </div>
                            {bar_html}
                            """, unsafe_allow_html=True)

                            if why:
                                st.markdown(f'<div class="article-card why-flagged">💡 <b>Why Flagged:</b> {why}</div>', unsafe_allow_html=True)

                            if show_article_text and body:
                                st.markdown(f"""
                                <div style="margin-top:0.75rem;font-size:0.83rem;color:#94a3b8;line-height:1.7;
                                            max-height:200px;overflow-y:auto;background:rgba(15,23,42,0.5);
                                            padding:0.75rem;border-radius:10px;border:1px solid rgba(51,65,85,0.4);">
                                    {body[:2000]}{'…' if len(body) > 2000 else ''}
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align:center;padding:2rem;color:#64748b;">
                        <div style="font-size:2rem;margin-bottom:0.5rem;">✅</div>
                        <div style="font-weight:600;color:#34d399;margin-bottom:0.25rem;">No adverse media findings</div>
                        <div style="font-size:0.85rem;">No articles above the relevance threshold were found for this entity.</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # ── Human Review ───────────────────────────────────────────
                st.markdown("""
                <div class="glass-card">
                    <div class="section-title">Human-in-the-Loop Review</div>
                """, unsafe_allow_html=True)

                notes = st.text_area(
                    "Analyst Notes",
                    placeholder="Add commentary, context, or justification for your decision…",
                    label_visibility="collapsed",
                    height=80,
                    key="analyst_notes",
                )

                b1, b2, b3 = st.columns(3)
                audit_payload = {
                    "screening_id": data["screening_id"],
                    "entity_name": data["entity"]["resolved_name"],
                    "analyst_notes": notes,
                    "risk_score": risk_score,
                    "risk_category": risk_cat,
                }

                with b1:
                    if st.button("✅  Approve / False Positive", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_payload, "action": "APPROVE"})
                        st.success("Logged: APPROVED")

                with b2:
                    if st.button("⚠️  Escalate to EDD", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_payload, "action": "ESCALATE"})
                        st.warning("Logged: ESCALATED")

                with b3:
                    if st.button("❌  Reject / Block", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_payload, "action": "REJECT"})
                        st.error("Logged: REJECTED")

                st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.error(f"Backend returned an error ({res.status_code}): {res.text[:300]}")

        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to the backend. Ensure FastAPI is running on port 8000.")
        except requests.exceptions.Timeout:
            st.warning("⏱️ Request timed out. Live news scraping can take up to 90 seconds — please retry.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

elif search_clicked and not query.strip():
    st.warning("Please enter an entity name to screen.")

else:
    # Empty State
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;animation:fadeIn 0.8s ease-out;">
        <div style="font-size:3.5rem;margin-bottom:1rem;filter:grayscale(0.3);">🔍</div>
        <div style="font-size:1.1rem;font-weight:600;color:#475569;margin-bottom:0.5rem;">
            Start by entering an entity name above
        </div>
        <div style="font-size:0.875rem;color:#334155;max-width:460px;margin:0 auto;line-height:1.7;">
            Search the adverse media database, or enable <b style="color:#94a3b8;">Fetch Recent News</b>
            to scrape live web results and run AI analysis.
        </div>
        <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin-top:2rem;">
            <span style="background:rgba(30,41,59,0.7);border:1px solid rgba(51,65,85,0.5);color:#64748b;font-size:0.8rem;padding:6px 16px;border-radius:999px;">Nexum Capital Partners</span>
            <span style="background:rgba(30,41,59,0.7);border:1px solid rgba(51,65,85,0.5);color:#64748b;font-size:0.8rem;padding:6px 16px;border-radius:999px;">Global Trade Solutions</span>
            <span style="background:rgba(30,41,59,0.7);border:1px solid rgba(51,65,85,0.5);color:#64748b;font-size:0.8rem;padding:6px 16px;border-radius:999px;">Marcus Holloway</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
