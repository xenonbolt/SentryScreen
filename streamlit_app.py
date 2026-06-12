import math
import streamlit as st
import requests

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentryScreen | Adverse Media Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #060d0d !important;
    color: #e2e8f0 !important;
}

/* Radial ambient glow */
[data-testid="stMain"]::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse at 15% 50%, rgba(16,185,129,0.07) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 10%, rgba(6,182,212,0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 90%, rgba(5,150,105,0.04) 0%, transparent 50%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(6, 15, 12, 0.97) !important;
    border-right: 1px solid rgba(16,185,129,0.18) !important;
}
[data-testid="stSidebar"] * { color: #a7f3d0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(16,185,129,0.12) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    color: #6ee7b7 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    padding: 0.55rem 1rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(16,185,129,0.22) !important;
    border-color: rgba(16,185,129,0.55) !important;
}

/* ── Main block ── */
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1380px !important;
}

/* ── Search input ── */
.stTextInput > div > div > input {
    background: rgba(6,20,16,0.85) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    border-radius: 14px !important;
    color: #f0fdf4 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(16,185,129,0.65) !important;
    box-shadow: 0 0 0 3px rgba(16,185,129,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #2d6a52 !important; }

/* ── Primary button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 20px rgba(16,185,129,0.3) !important;
    transition: all 0.2s !important;
    letter-spacing: 0.02em !important;
    height: 100% !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #047857, #059669) !important;
    box-shadow: 0 6px 28px rgba(16,185,129,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary buttons ── */
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background: rgba(16,185,129,0.08) !important;
    border: 1px solid rgba(16,185,129,0.25) !important;
    border-radius: 12px !important;
    color: #6ee7b7 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {
    background: rgba(16,185,129,0.18) !important;
    border-color: rgba(16,185,129,0.5) !important;
}

/* ── Checkbox ── */
.stCheckbox > label { color: #6ee7b7 !important; font-size: 0.85rem !important; }

/* ── st.metric ── */
[data-testid="metric-container"] {
    background: rgba(6,20,16,0.80) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-radius: 16px !important;
    padding: 1.1rem 1.3rem !important;
}
[data-testid="stMetricLabel"] {
    color: #34d399 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    color: #f0fdf4 !important;
    font-size: 1.9rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: rgba(6,20,16,0.60) !important;
    border: 1px solid rgba(16,185,129,0.18) !important;
    border-radius: 14px !important;
    margin-bottom: 0.6rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    color: #a7f3d0 !important;
    font-size: 0.87rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
}
[data-testid="stExpander"] summary:hover { background: rgba(16,185,129,0.07) !important; }
[data-testid="stExpander"] > div > div { color: #cbd5e1 !important; }

/* ── Text area ── */
.stTextArea > div > div > textarea {
    background: rgba(6,20,16,0.8) !important;
    border: 1px solid rgba(16,185,129,0.25) !important;
    border-radius: 12px !important;
    color: #d1fae5 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.87rem !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: rgba(16,185,129,0.55) !important;
    box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important;
}
.stTextArea > div > div > textarea::placeholder { color: #1a4a38 !important; }
label[data-testid="stWidgetLabel"] { color: #34d399 !important; font-size: 0.82rem !important; }

/* ── Divider ── */
hr { border-color: rgba(16,185,129,0.15) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 12px !important; font-family: 'Inter', sans-serif !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #060d0d; }
::-webkit-scrollbar-thumb { background: #134e37; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #10b981; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #10b981 !important; }

/* ── Animations ── */
@keyframes fadeIn  { from { opacity:0; }                       to { opacity:1; } }
@keyframes slideUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
@keyframes pulse   { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.5;transform:scale(.75);} }

/* ── Custom HTML classes ── */
.ss-card {
    background: rgba(6,20,16,0.70);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 20px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1.1rem;
    animation: slideUp 0.4s ease-out;
}
.ss-card-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #059669;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(16,185,129,0.12);
}
.gradient-text {
    background: linear-gradient(135deg, #34d399 0%, #22d3ee 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.badge {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.badge-CRITICAL { background:rgba(190,18,60,0.2);  color:#fb7185; border:1px solid rgba(190,18,60,0.4); }
.badge-HIGH     { background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.35); }
.badge-MEDIUM   { background:rgba(245,158,11,0.15);color:#fcd34d; border:1px solid rgba(245,158,11,0.35); }
.badge-LOW      { background:rgba(16,185,129,0.15);color:#34d399; border:1px solid rgba(16,185,129,0.35); }
.cat-HIGH   { background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.35); }
.cat-MEDIUM { background:rgba(245,158,11,0.12);color:#fcd34d; border:1px solid rgba(245,158,11,0.35); }
.cat-LOW    { background:rgba(16,185,129,0.12);color:#34d399; border:1px solid rgba(16,185,129,0.35); }
.alias-tag {
    display:inline-block;
    background:rgba(6,30,20,0.8);
    border:1px solid rgba(16,185,129,0.2);
    color:#6ee7b7;
    font-size:0.72rem;
    padding:2px 10px;
    border-radius:999px;
    margin:2px;
}
.kw-tag {
    display:inline-block;
    background:rgba(6,182,212,0.1);
    border:1px solid rgba(6,182,212,0.25);
    color:#67e8f9;
    font-size:0.73rem;
    font-weight:500;
    padding:3px 10px;
    border-radius:999px;
    margin:3px 3px 3px 0;
}
.summary-box {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    color: #d1fae5;
    font-size: 0.88rem;
    line-height: 1.75;
}
.why-flagged {
    background: rgba(16,185,129,0.06);
    border-left: 3px solid rgba(16,185,129,0.45);
    border-radius: 0 10px 10px 0;
    padding: 0.5rem 0.8rem;
    color: #a7f3d0;
    font-size: 0.82rem;
    line-height: 1.6;
    margin-top: 0.5rem;
}
.art-body {
    margin-top: 0.75rem;
    font-size: 0.82rem;
    color: #6ee7b7;
    line-height: 1.7;
    max-height: 200px;
    overflow-y: auto;
    background: rgba(4,12,9,0.6);
    padding: 0.75rem;
    border-radius: 10px;
    border: 1px solid rgba(16,185,129,0.12);
}
.live-badge {
    display:inline-flex;
    align-items:center;
    gap:5px;
    background:rgba(239,68,68,0.1);
    border:1px solid rgba(239,68,68,0.3);
    color:#f87171;
    font-size:0.68rem;
    font-weight:700;
    padding:2px 9px;
    border-radius:999px;
    letter-spacing:0.05em;
    vertical-align:middle;
}
.live-dot {
    width:6px; height:6px;
    background:#f87171;
    border-radius:50%;
    animation:pulse 1.5s ease-in-out infinite;
    display:inline-block;
}
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    animation: fadeIn 0.8s ease-out;
}
.empty-state .icon { font-size:3.5rem; margin-bottom:1rem; filter:grayscale(0.2); }
.empty-state .title { font-size:1.05rem; font-weight:600; color:#2d6a52; margin-bottom:0.5rem; }
.empty-state .sub { font-size:0.875rem; color:#1a4a38; max-width:440px; margin:0 auto; line-height:1.7; }
.example-tag {
    display:inline-block;
    background:rgba(6,20,16,0.8);
    border:1px solid rgba(16,185,129,0.18);
    color:#2d6a52;
    font-size:0.78rem;
    padding:5px 14px;
    border-radius:999px;
    margin:4px;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api"


def sev_badge(sev: str) -> str:
    s = sev.upper()
    return f'<span class="badge badge-{s}">{s}</span>'


def bar_html(val: float, color: str = "#10b981") -> str:
    pct = min(100, val * 100)
    return (
        f'<div style="background:rgba(16,185,129,0.08);border-radius:999px;height:5px;overflow:hidden;margin-top:4px;">'
        f'<div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:999px;transition:width 0.8s;"></div>'
        f'</div>'
    )


def risk_color(cat: str):
    return {"HIGH": ("#f87171", "#ef4444"), "MEDIUM": ("#fcd34d", "#f59e0b"), "LOW": ("#34d399", "#10b981")}.get(cat, ("#34d399", "#10b981"))


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.25rem 0 0.75rem;">
        <div style="display:inline-flex;align-items:center;justify-content:center;
                    width:60px;height:60px;background:rgba(16,185,129,0.1);
                    border:1px solid rgba(16,185,129,0.25);border-radius:18px;
                    font-size:1.8rem;margin-bottom:0.6rem;">🛡️</div>
        <div style="font-size:1.15rem;font-weight:800;color:#d1fae5;letter-spacing:-0.02em;">SentryScreen</div>
        <div style="font-size:0.75rem;color:#065f46;margin-top:3px;font-weight:500;">Adverse Media Copilot</div>
    </div>
    <hr style="border-color:rgba(16,185,129,0.12);margin:0.5rem 0 1rem;">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#065f46;margin-bottom:0.75rem;">
        System Status
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄  Refresh Backend Status", use_container_width=True):
        try:
            health = requests.get(f"{API_BASE}/health", timeout=5).json()
            stats  = requests.get(f"{API_BASE}/dataset-stats", timeout=5).json()
            st.success("✓ Backend Connected")
            st.markdown(f"""
            <div style="font-size:0.8rem;color:#6ee7b7;line-height:2;margin-top:0.4rem;">
                <div>🖥 <b style="color:#a7f3d0;">Device:</b> {health.get('device','?').upper()}</div>
                <div>⚡ <b style="color:#a7f3d0;">Hardware:</b> {health.get('device_name','?')}</div>
                <div>📰 <b style="color:#a7f3d0;">Articles:</b> {stats.get('total_articles',0):,}</div>
                <div>🏢 <b style="color:#a7f3d0;">Entities:</b> {stats.get('unique_entities',0)}</div>
                <div>📦 <b style="color:#a7f3d0;">Version:</b> {health.get('version','?')}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("⚠️ Backend Offline — ensure FastAPI is running on port 8000.")

    st.markdown("""
    <hr style="border-color:rgba(16,185,129,0.12);margin:1rem 0;">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#065f46;margin-bottom:0.6rem;">
        Risk Thresholds
    </div>
    <div style="font-size:0.8rem;line-height:2.1;color:#6ee7b7;">
        <div>🔴 <b style="color:#f87171;">HIGH</b> &nbsp; Score &gt; 70</div>
        <div>🟡 <b style="color:#fcd34d;">MEDIUM</b> &nbsp; Score 30–70</div>
        <div>🟢 <b style="color:#34d399;">LOW</b> &nbsp; Score &lt; 30</div>
    </div>
    <hr style="border-color:rgba(16,185,129,0.12);margin:1rem 0;">
    <div style="font-size:0.68rem;color:#064e3b;text-align:center;padding-bottom:0.5rem;line-height:1.6;">
        AMD ROCm · FAISS · SentenceTransformers
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-bottom:2rem;animation:fadeIn 0.6s ease-out;">
    <div style="display:inline-flex;align-items:center;justify-content:center;
                width:76px;height:76px;background:rgba(16,185,129,0.1);
                border:1px solid rgba(16,185,129,0.22);border-radius:22px;
                font-size:2.2rem;margin-bottom:1rem;box-shadow:0 0 32px rgba(16,185,129,0.12);">🛡️</div>
    <h1 style="font-size:2.6rem;font-weight:800;letter-spacing:-0.035em;
               color:#f0fdf4;margin:0 0 0.4rem;line-height:1.15;">
        SentryScreen <span class="gradient-text">Copilot</span>
    </h1>
    <p style="color:#065f46;font-size:0.95rem;margin:0;">
        AI-powered adverse media screening · Vector similarity · Explainable risk scoring
    </p>
</div>
""", unsafe_allow_html=True)

# ── Search ────────────────────────────────────────────────────────────────────
col_inp, col_btn = st.columns([5, 1])
with col_inp:
    query = st.text_input(
        label="search",
        label_visibility="collapsed",
        placeholder="🔍  Enter company or person name — e.g. Nexum Capital Partners",
        key="search_query",
    )
with col_btn:
    screen_clicked = st.button("Screen ➜", type="primary", use_container_width=True)

chk1, chk2, _ = st.columns([2, 2, 4])
with chk1:
    use_live_web      = st.checkbox("🌐  Fetch Recent News", value=True, help="Real-time DuckDuckGo search + AI analysis")
with chk2:
    show_article_text = st.checkbox("📄  Show Article Text", value=True)

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

# ── Main Logic ────────────────────────────────────────────────────────────────
if screen_clicked and query.strip():
    spin_msg = (
        f"Fetching recent news for **{query}** and running AI analysis…"
        if use_live_web
        else f"Screening **{query}** across the adverse media database…"
    )

    with st.spinner(spin_msg):
        try:
            res = requests.post(
                f"{API_BASE}/screen",
                json={"entity_name": query.strip(), "top_k": 10, "threshold": 0.15, "use_live_web": use_live_web},
                timeout=90,
            )

            if res.status_code != 200:
                st.error(f"Backend error ({res.status_code}): {res.text[:300]}")
            else:
                data       = res.json()
                risk_cat   = data["risk_category"]
                risk_score = data["risk_score"]
                confidence = data["confidence_score"]
                articles   = data.get("articles", [])
                expl       = data.get("explainability", {})
                breakdown  = data.get("risk_breakdown", {})
                entity     = data["entity"]

                rc_text, rc_glow = risk_color(risk_cat)

                # ── Resolution Banner ─────────────────────────────────────
                mode_html = (
                    '<span class="live-badge"><span class="live-dot"></span>LIVE NEWS</span>'
                    if use_live_web else
                    '<span style="font-size:0.75rem;color:#065f46;font-weight:500;">Dataset search</span>'
                )
                aliases_html = "".join(
                    f'<span class="alias-tag">{a}</span>'
                    for a in (entity.get("aliases") or [])
                )
                st.markdown(f"""
                <div class="ss-card" style="display:flex;align-items:center;justify-content:space-between;
                     flex-wrap:wrap;gap:0.75rem;padding:1rem 1.4rem;margin-bottom:1rem;">
                    <div>
                        <div style="font-size:0.8rem;color:#065f46;margin-bottom:3px;">
                            Queried: <span style="color:#d1fae5;font-weight:600;">{entity['original_name']}</span>
                            &nbsp;{mode_html}
                        </div>
                        <div style="font-size:0.85rem;color:#6ee7b7;">
                            Resolved to:
                            <span style="color:#34d399;font-weight:700;">{entity['resolved_name']}</span>
                            <span style="color:#065f46;margin-left:0.5rem;">·</span>
                            <span style="color:#065f46;font-size:0.78rem;margin-left:0.4rem;">
                                Confidence {entity['confidence']*100:.1f}%
                            </span>
                        </div>
                    </div>
                    <div>{aliases_html}</div>
                </div>
                """, unsafe_allow_html=True)

                # ── Metrics ───────────────────────────────────────────────
                cat_emoji = "🔴" if risk_cat == "HIGH" else "🟡" if risk_cat == "MEDIUM" else "🟢"
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Risk Score",       f"{risk_score:.1f} / 100", f"{cat_emoji} {risk_cat}", delta_color="off")
                m2.metric("Confidence",        f"{confidence*100:.1f}%")
                m3.metric("Articles Flagged",  data["total_articles_found"])
                m4.metric("Processing Time",   f"{data.get('processing_time_ms', 0):.0f} ms")

                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

                # ── Gauge + Breakdown (left) | Explainability (right) ─────
                g_col, e_col = st.columns([4, 8])

                with g_col:
                    # SVG arc gauge — fully self-contained
                    pct   = risk_score / 100
                    angle = pct * 180
                    theta = math.radians(180 - angle)
                    cx, cy, r = 90, 88, 68
                    ex = cx + r * math.cos(theta)
                    ey = cy - r * math.sin(theta)

                    bk = {
                        "Relevance":  (breakdown.get("relevance_contribution",  0), "#10b981"),
                        "Severity":   (breakdown.get("severity_contribution",   0), "#f87171"),
                        "Frequency":  (breakdown.get("frequency_contribution",  0), "#fbbf24"),
                        "Recency":    (breakdown.get("recency_contribution",    0), "#22d3ee"),
                    }
                    breakdown_rows = "".join(
                        f"""<div style="margin-bottom:0.55rem;">
                                <div style="display:flex;justify-content:space-between;
                                            font-size:0.77rem;color:#6ee7b7;margin-bottom:3px;">
                                    <span>{lbl}</span>
                                    <span style="color:{clr};font-weight:700;">{val*100:.1f}</span>
                                </div>
                                <div style="background:rgba(16,185,129,0.08);border-radius:999px;height:5px;overflow:hidden;">
                                    <div style="width:{min(val*100,100):.1f}%;height:100%;background:{clr};border-radius:999px;"></div>
                                </div>
                            </div>"""
                        for lbl, (val, clr) in bk.items()
                    )

                    st.markdown(f"""
                    <div class="ss-card" style="text-align:center;">
                        <div class="ss-card-title" style="text-align:left;">Risk Score</div>
                        <svg viewBox="0 0 180 108" width="100%" style="max-width:210px;display:block;margin:0 auto 0.25rem;">
                            <defs>
                                <filter id="glow">
                                    <feGaussianBlur stdDeviation="3" result="blur"/>
                                    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                                </filter>
                            </defs>
                            <path d="M 22 90 A 68 68 0 0 1 158 90"
                                  fill="none" stroke="rgba(16,185,129,0.1)" stroke-width="11" stroke-linecap="round"/>
                            <path d="M 22 90 A 68 68 0 0 1 {ex:.2f} {ey:.2f}"
                                  fill="none" stroke="{rc_glow}" stroke-width="11" stroke-linecap="round"
                                  filter="url(#glow)"/>
                            <text x="90" y="78" text-anchor="middle" font-size="27" font-weight="800"
                                  fill="#f0fdf4" font-family="Inter,sans-serif">{risk_score:.0f}</text>
                            <text x="90" y="96" text-anchor="middle" font-size="9.5"
                                  fill="#065f46" font-family="Inter,sans-serif">out of 100</text>
                        </svg>
                        <div style="margin:0.1rem auto 0.9rem;">
                            <span style="display:inline-block;padding:3px 16px;border-radius:999px;
                                         font-size:0.75rem;font-weight:700;letter-spacing:0.07em;"
                                  class="cat-{risk_cat}">{risk_cat} RISK</span>
                        </div>
                        <div style="text-align:left;">
                            <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#065f46;
                                        margin-bottom:0.6rem;padding-bottom:0.4rem;
                                        border-bottom:1px solid rgba(16,185,129,0.1);">
                                Risk Breakdown
                            </div>
                            {breakdown_rows}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with e_col:
                    # Keywords
                    kw_html = " ".join(
                        f'<span class="kw-tag">{kw}</span>'
                        for kw in expl.get("top_keywords", [])
                    )
                    # Risk factors
                    factors_html = "".join(
                        f"""<div style="display:flex;align-items:flex-start;gap:0.5rem;
                                        padding:0.5rem 0;border-bottom:1px solid rgba(16,185,129,0.08);
                                        font-size:0.84rem;color:#a7f3d0;line-height:1.55;">
                                <span style="color:#f87171;flex-shrink:0;margin-top:2px;">▸</span>
                                <span>{f}</span>
                            </div>"""
                        for f in expl.get("key_risk_factors", [])
                    )

                    st.markdown(f"""
                    <div class="ss-card">
                        <div class="ss-card-title">Executive Summary</div>
                        <div class="summary-box">
                            {expl.get('summary', 'No summary available.')}
                        </div>
                        <div style="margin:1rem 0 0.5rem;">
                            <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#065f46;margin-bottom:0.55rem;">
                                Top Keywords
                            </div>
                            <div>{kw_html if kw_html else '<span style="color:#1a4a38;font-size:0.82rem;">None identified</span>'}</div>
                        </div>
                        {f'''<div style="margin-top:0.9rem;">
                            <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#065f46;margin-bottom:0.3rem;">
                                Key Risk Factors
                            </div>
                            {factors_html}
                        </div>''' if factors_html else ''}
                    </div>
                    """, unsafe_allow_html=True)

                # ── Articles Section ──────────────────────────────────────
                art_count = len(articles)
                st.markdown(f"""
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#059669;
                            margin-bottom:0.6rem;padding:0 0.2rem;
                            display:flex;justify-content:space-between;align-items:center;">
                    <span>Adverse Media Findings</span>
                    <span style="color:#065f46;font-weight:500;font-size:0.78rem;
                                 text-transform:none;letter-spacing:0;">
                        {art_count} article{'s' if art_count != 1 else ''} found
                    </span>
                </div>
                """, unsafe_allow_html=True)

                if articles:
                    for art in articles:
                        sev        = art.get("severity_label", "LOW").upper()
                        rel        = art.get("relevance_score", 0)
                        title      = art.get("article_title", "Untitled")
                        date_str   = (art.get("published_date") or "")[:10] or "Unknown date"
                        src        = art.get("source", "")
                        src_disp   = src.split("/")[2] if src.startswith("http") and len(src.split("/")) > 2 else src or "Unknown"
                        category   = art.get("category", "")
                        why        = art.get("why_flagged", "")
                        body       = art.get("article_text", "")

                        cat_tag    = f'<span style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);color:#6ee7b7;font-size:0.68rem;padding:2px 8px;border-radius:999px;margin-left:4px;">{category}</span>' if category else ""
                        bar        = bar_html(rel)
                        why_block  = f'<div class="why-flagged">💡 <b>Why flagged:</b> {why}</div>' if why else ""
                        body_block = f'<div class="art-body">{body[:2000]}{"…" if len(body) > 2000 else ""}</div>' if show_article_text and body else ""

                        src_link = (
                            f'<a href="{src}" target="_blank" rel="noopener noreferrer" '
                            f'style="color:#34d399;text-decoration:none;font-size:0.73rem;'
                            f'border-bottom:1px dashed rgba(52,211,153,0.4);">{src_disp}</a>'
                            if src.startswith("http") else
                            f'<span style="font-size:0.73rem;color:#065f46;">{src_disp}</span>'
                        )
                        with st.expander(f"{sev} · {title}", expanded=False):
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:0.5rem;
                                        flex-wrap:wrap;margin-bottom:0.6rem;">
                                {sev_badge(sev)}{cat_tag}
                                <span style="font-size:0.73rem;color:#065f46;">📅 {date_str}</span>
                                <span style="font-size:0.73rem;color:#065f46;">🔗&nbsp;{src_link}</span>
                                <span style="font-size:0.73rem;color:#6ee7b7;margin-left:auto;">
                                    Relevance: <b style="color:#34d399;">{rel:.3f}</b>
                                </span>
                            </div>
                            {bar}
                            {why_block}
                            {body_block}
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align:center;padding:2.5rem 1rem;">
                        <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
                        <div style="font-weight:700;color:#34d399;margin-bottom:0.3rem;font-size:1rem;">No adverse media findings</div>
                        <div style="font-size:0.84rem;color:#065f46;">No articles above the relevance threshold were found for this entity.</div>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Human Review ──────────────────────────────────────────
                st.markdown("""
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#059669;
                            margin:1.25rem 0 0.6rem;padding:0 0.2rem;">
                    Human-in-the-Loop Review
                </div>
                """, unsafe_allow_html=True)

                notes = st.text_area(
                    "Analyst Notes",
                    placeholder="Add commentary, context, or justification for your decision…",
                    height=80,
                    key="analyst_notes",
                )

                b1, b2, b3 = st.columns(3)
                audit_base = {
                    "screening_id": data["screening_id"],
                    "entity_name":  entity["resolved_name"],
                    "analyst_notes": notes,
                    "risk_score":   risk_score,
                    "risk_category": risk_cat,
                }

                with b1:
                    if st.button("✅  Approve / False Positive", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "APPROVE"})
                        st.success("Logged: APPROVED")
                with b2:
                    if st.button("⚠️  Escalate to EDD", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "ESCALATE"})
                        st.warning("Logged: ESCALATED")
                with b3:
                    if st.button("❌  Reject / Block", use_container_width=True):
                        requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "REJECT"})
                        st.error("Logged: REJECTED")

        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot reach the backend. Ensure FastAPI is running on port 8000.")
        except requests.exceptions.Timeout:
            st.warning("⏱️ Request timed out. Live news scraping can take up to 90s — please retry.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

elif screen_clicked and not query.strip():
    st.warning("Please enter an entity name to screen.")

else:
    # ── Empty State ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🔍</div>
        <div class="title">Enter an entity name above to begin screening</div>
        <div class="sub">
            Search the adverse media database, or enable
            <b style="color:#34d399;">Fetch Recent News</b>
            to scrape live web results and run AI-powered risk analysis.
        </div>
        <div style="margin-top:1.75rem;">
            <span class="example-tag">Nexum Capital Partners</span>
            <span class="example-tag">Global Trade Solutions</span>
            <span class="example-tag">Viktor Dragan</span>
            <span class="example-tag">Marcus Holloway</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
