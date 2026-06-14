import math
import streamlit as st
import requests
import pandas as pd
import random
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentryScreen | Advanced Threat Copilot",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "recent_sessions" not in st.session_state:
    st.session_state.recent_sessions = []

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0d0d0d !important;
    color: #e2e8f0 !important;
}

/* Radial ambient glow - subtle red + a hint of green */
[data-testid="stMain"]::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse at 15% 50%, rgba(229,56,59,0.06) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 10%, rgba(34,197,94,0.03) 0%, transparent 40%),
        radial-gradient(ellipse at 50% 90%, rgba(229,56,59,0.03) 0%, transparent 50%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080808 !important;
    border-right: 1px solid rgba(229,56,59,0.18) !important;
}
[data-testid="stSidebar"] * { color: #f87171 !important; }

/* ── Main block ── */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1440px !important;
}

/* ── Custom fonts ── */
.mono-data {
    font-family: 'Fira Code', 'Consolas', monospace !important;
    letter-spacing: 0.05em;
}

/* ── Search inputs ── */
.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid rgba(229,56,59,0.3) !important;
    border-radius: 10px !important;
    color: #f87171 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(229,56,59,0.8) !important;
    box-shadow: 0 0 0 3px rgba(229,56,59,0.15) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #6b2121 !important; }

/* ── Primary button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #ba1826, #e5383b) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 15px rgba(229,56,59,0.3) !important;
    transition: all 0.2s !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    height: 100% !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #a41623, #ba1826) !important;
    box-shadow: 0 6px 20px rgba(229,56,59,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary buttons ── */
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background: rgba(229,56,59,0.08) !important;
    border: 1px solid rgba(229,56,59,0.25) !important;
    border-radius: 8px !important;
    color: #fca5a5 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {
    background: rgba(229,56,59,0.18) !important;
    border-color: rgba(229,56,59,0.6) !important;
}

/* ── Tabs ── */
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #94a3b8 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 2px solid transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #e5383b !important;
    border-bottom: 2px solid #e5383b !important;
    background: rgba(229,56,59,0.05) !important;
}

/* ── st.metric ── */
[data-testid="metric-container"] {
    background: #111827 !important;
    border: 1px solid rgba(229,56,59,0.2) !important;
    border-left: 4px solid #e5383b !important;
    border-radius: 8px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] {
    color: #f87171 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    font-family: 'Fira Code', monospace !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid rgba(229,56,59,0.2) !important;
    border-radius: 8px !important;
    margin-bottom: 0.6rem !important;
}
[data-testid="stExpander"] summary {
    color: #fca5a5 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.85rem !important;
}

/* ── Text area ── */
.stTextArea > div > div > textarea {
    background: #111827 !important;
    border: 1px solid rgba(229,56,59,0.3) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea > div > div > textarea:focus { border-color: #e5383b !important; }

/* ── Divider ── */
hr { border-color: rgba(229,56,59,0.15) !important; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
    background: #111827 !important;
    border: 1px solid rgba(229,56,59,0.2) !important;
}

/* ── Custom Cards ── */
.ss-card {
    background: #111827;
    border: 1px solid rgba(229,56,59,0.2);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.ss-card-title {
    font-family: 'Fira Code', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #e5383b;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(229,56,59,0.2);
}
/* A green accented card title */
.ss-card-title-green {
    font-family: 'Fira Code', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #22c55e;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(34, 197, 94, 0.2);
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-CRITICAL { background:rgba(220,38,38,0.2);  color:#f87171; border:1px solid rgba(220,38,38,0.5); }
.badge-HIGH     { background:rgba(239,68,68,0.15); color:#fca5a5; border:1px solid rgba(239,68,68,0.4); }
.badge-MEDIUM   { background:rgba(245,158,11,0.15);color:#fcd34d; border:1px solid rgba(245,158,11,0.4); }
.badge-LOW      { background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.4); }

.cat-HIGH   { background:rgba(220,38,38,0.2);  color:#f87171; border:1px solid rgba(220,38,38,0.5); }
.cat-MEDIUM { background:rgba(245,158,11,0.15);color:#fcd34d; border:1px solid rgba(245,158,11,0.4); }
.cat-LOW    { background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.4); }

.alias-tag, .kw-tag {
    display:inline-block;
    background:rgba(229,56,59,0.1);
    border:1px solid rgba(229,56,59,0.3);
    color:#fca5a5;
    font-size:0.75rem;
    padding:3px 10px;
    border-radius:4px;
    margin:3px;
    font-family: 'Fira Code', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── Constants & Helpers ───────────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api"

def risk_color(cat: str):
    return {"HIGH": ("#ef4444", "#dc2626"), "MEDIUM": ("#f59e0b", "#d97706"), "LOW": ("#22c55e", "#16a34a")}.get(cat, ("#22c55e", "#16a34a"))

def sev_badge(sev: str) -> str:
    s = sev.upper()
    return f'<span class="badge badge-{s}">{s}</span>'

# We no longer mock ROCm logic here since the backend provides real VRAM/load via /health
if "vram_usage" not in st.session_state:
    st.session_state.vram_usage = 0
    st.session_state.compute_load = 0

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;">
    <div style="font-size:2.5rem;color:#e5383b;">🩸</div>
    <div>
        <h1 style="font-size:1.8rem;font-weight:800;color:#f8fafc;margin:0;letter-spacing:0.05em;text-transform:uppercase;">
            SentryScreen <span style="color:#e5383b;">Copilot</span>
        </h1>
        <div style="font-family:'Fira Code', monospace;color:#fca5a5;font-size:0.8rem;">
            Advanced Threat Intelligence
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs Navigation ───────────────────────────────────────────────────────────
tab_screen, tab_audit, tab_comp, tab_rocm = st.tabs([
    "🎯 Screening Hub", 
    "📜 Audit Logs", 
    "🗄️ Compliance Database", 
    "⚙️ ROCm GPU Diagnostics"
])


# ==============================================================================
# TAB: SCREENING HUB
# ==============================================================================
with tab_screen:
    
    # ── Search & Controls ──
    search_col1, search_col2, search_col3 = st.columns([4, 4, 2])
    with search_col1:
        query = st.text_input("ENTITY NAME", placeholder="e.g. Nexum Capital Partners", key="search_query")
    with search_col2:
        focus = st.text_input("CUSTOM THREAT FOCUS (Optional)", placeholder="e.g. Money Laundering, Cyber", key="threat_focus")
    with search_col3:
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        screen_clicked = st.button("EXECUTE SCREENING ➜", type="primary", use_container_width=True)
        
    chk1, chk2 = st.columns([3, 9])
    with chk1:
        use_live_web = st.checkbox("🌐 LIVE WEB OSINT", value=True)
    with chk2:
        if use_live_web:
            search_engine = st.radio("Search Engine", ["DuckDuckGo", "Google"], horizontal=True, label_visibility="collapsed")
        else:
            search_engine = "DuckDuckGo"
        
    if st.session_state.recent_sessions:
        st.markdown(f"<div style='font-family:\"Fira Code\", monospace;font-size:0.75rem;color:#fca5a5;'>RECENT SESSIONS: <span style='color:#e2e8f0;'>{' | '.join(st.session_state.recent_sessions[-5:])}</span></div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)

    if screen_clicked and query.strip():
        if query.strip() not in st.session_state.recent_sessions:
            st.session_state.recent_sessions.append(query.strip())
            
        with st.spinner("INITIATING THREAT ANALYSIS PIPELINE..."):
            try:
                res = requests.post(
                    f"{API_BASE}/screen",
                    json={"entity_name": query.strip(), "top_k": 15, "threshold": 0.0, "use_live_web": use_live_web, "search_engine": search_engine.lower()},
                    timeout=90,
                )
                
                if res.status_code != 200:
                    try:
                        err_detail = res.json().get("detail", res.text)
                        st.error(f"Error: {err_detail}")
                    except ValueError:
                        st.error(f"SYS_ERROR: {res.text}")
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
                    
                    # ── 3-Panel Layout ──
                    p1, p2, p3 = st.columns([3, 3, 3])
                    
                    with p1:
                        aliases_html = "".join(f'<span class="alias-tag">{a}</span>' for a in (entity.get("aliases") or []))
                        st.markdown(f"""
                        <div class="ss-card" style="height:100%;">
                            <div class="ss-card-title">ENTITY RESOLUTION</div>
                            <div style="margin-bottom:1rem;font-family:'Fira Code', monospace;font-size:0.8rem;color:#fca5a5;">
                                INPUT: <span style="color:#f8fafc;">{entity['original_name']}</span>
                            </div>
                            <div style="margin-bottom:1rem;font-family:'Fira Code', monospace;font-size:0.8rem;color:#fca5a5;">
                                RESOLVED TO: <br>
                                <span style="color:#e5383b;font-size:1.1rem;font-weight:700;">{entity['resolved_name']}</span>
                            </div>
                            <div style="margin-bottom:1rem;font-family:'Fira Code', monospace;font-size:0.8rem;color:#fca5a5;">
                                CONFIDENCE: <span style="color:#f8fafc;">{entity['confidence']*100:.1f}%</span>
                            </div>
                            <div style="font-family:'Fira Code', monospace;font-size:0.8rem;color:#fca5a5;margin-bottom:0.5rem;">KNOWN ALIASES:</div>
                            <div>{aliases_html or '<span style="color:#6b2121;font-size:0.8rem;">[NONE DETECTED]</span>'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with p2:
                        pct   = risk_score / 100
                        angle = pct * 180
                        theta = math.radians(180 - angle)
                        cx, cy, r = 90, 88, 68
                        ex = cx + r * math.cos(theta)
                        ey = cy - r * math.sin(theta)
                        
                        bk = {
                            "Relevance":  (breakdown.get("relevance_component",  0)/30, "#ba1826"),
                            "Severity":   (breakdown.get("severity_component",   0)/22, "#dc2626"),
                            "Frequency":  (breakdown.get("frequency_component",  0)/20, "#fca5a5"),
                            "Recency":    (breakdown.get("recency_component",    0)/13, "#ef4444"),
                            "Sentiment":  (breakdown.get("sentiment_component",  0)/15, "#f59e0b"),
                        }
                        breakdown_rows = "".join(
                            f"""<div style="margin-bottom:0.5rem;">
                                    <div style="display:flex;justify-content:space-between;font-family:'Fira Code', monospace;font-size:0.7rem;color:#fca5a5;margin-bottom:3px;">
                                        <span>{lbl}</span><span style="color:{clr};">{val*100:.1f}%</span>
                                    </div>
                                    <div style="background:#000;border:1px solid #333;height:6px;">
                                        <div style="width:{min(val*100,100):.1f}%;height:100%;background:{clr};"></div>
                                    </div>
                                </div>"""
                            for lbl, (val, clr) in bk.items()
                        )
                        
                        st.markdown(f"""
                        <div class="ss-card" style="text-align:center;height:100%;">
                            <div class="ss-card-title" style="text-align:left;">THREAT GAUGE</div>
                            <svg viewBox="0 0 180 108" width="100%" style="max-width:210px;display:block;margin:0 auto;">
                                <path d="M 22 90 A 68 68 0 0 1 158 90" fill="none" stroke="#333" stroke-width="11" stroke-linecap="round"/>
                                <path d="M 22 90 A 68 68 0 0 1 {ex:.2f} {ey:.2f}" fill="none" stroke="{rc_glow}" stroke-width="11" stroke-linecap="round"/>
                                <text x="90" y="78" text-anchor="middle" font-size="28" font-weight="800" fill="#f8fafc" font-family="'Fira Code', monospace">{risk_score:.0f}</text>
                                <text x="90" y="96" text-anchor="middle" font-size="10" fill="#fca5a5" font-family="'Fira Code', monospace">RISK SCORE</text>
                            </svg>
                            <div style="margin:0 auto 1rem;">
                                <span style="display:inline-block;padding:4px 16px;border-radius:4px;font-family:'Fira Code',monospace;font-size:0.8rem;font-weight:700;letter-spacing:0.1em;" class="cat-{risk_cat}">{risk_cat} RISK</span>
                            </div>
                            <div style="text-align:left;">{breakdown_rows}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with p3:
                        kw_html = " ".join(f'<span class="kw-tag">{kw}</span>' for kw in expl.get("top_keywords", []))
                        factors_html = "".join(
                            f"""<div style="display:flex;gap:0.5rem;margin-bottom:0.4rem;font-size:0.8rem;color:#e2e8f0;line-height:1.4;">
                                    <span style="color:#e5383b;">▶</span><span>{f}</span>
                                </div>"""
                            for f in expl.get("key_risk_factors", [])
                        )
                        
                        st.markdown(f"""
                        <div class="ss-card" style="height:100%;">
                            <div class="ss-card-title">COMPLIANCE DIRECTIVE</div>
                            <div style="font-size:0.85rem;color:#f1f5f9;line-height:1.6;margin-bottom:1rem;background:rgba(229,56,59,0.05);padding:1rem;border-left:3px solid #e5383b;">
                                {expl.get('summary', 'No summary available.')}
                            </div>
                            <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:#e5383b;margin-bottom:0.5rem;">RISK FACTORS:</div>
                            <div style="margin-bottom:1rem;">{factors_html}</div>
                            <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:#e5383b;margin-bottom:0.5rem;">EXTRACTED KEYWORDS:</div>
                            <div>{kw_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # ── Publication Cards ──
                    art_count = len(articles)
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;margin:2rem 0 1rem;">
                        <div class="ss-card-title" style="margin:0;border:none;">MATCHED PUBLICATIONS</div>
                        <div style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#fca5a5;">TOTAL DETECTED: {art_count}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if art_count == 0:
                        st.markdown("<div style='color:#6b2121;font-family:\"Fira Code\",monospace;'>[NO PUBLICATIONS DETECTED EVEN WITH 0.0 THRESHOLD]</div>", unsafe_allow_html=True)
                        
                    for art in articles:
                        sev = art.get("severity_label", "LOW").upper()
                        rel = art.get("relevance_score", 0)
                        title = art.get("article_title", "Untitled")
                        date_str = (art.get("published_date") or "")[:10] or "Unknown date"
                        src = art.get("source", "")
                        why = art.get("why_flagged", "")
                        body = art.get("article_text", "")
                        
                        pct = min(100, rel * 100)
                        bar = f'<div style="background:#000;border:1px solid #333;height:4px;margin-top:6px;"><div style="width:{pct:.1f}%;height:100%;background:#e5383b;"></div></div>'
                        
                        with st.expander(f"{sev} | MATCH: {pct:.1f}% | {title}", expanded=False):
                            st.markdown(f"""
                            <div style="margin-bottom:0.8rem;font-family:'Fira Code',monospace;font-size:0.75rem;color:#fca5a5;">
                                DATE: <span style="color:#f8fafc;">{date_str}</span> | SOURCE: <span style="color:#f8fafc;">{src}</span>
                            </div>
                            {sev_badge(sev)}
                            <div style="margin:0.8rem 0;font-size:0.85rem;color:#f1f5f9;background:rgba(229,56,59,0.05);padding:0.75rem;border-left:2px solid #e5383b;">
                                <strong style="color:#e5383b;">WHY FLAGGED:</strong> {why}
                            </div>
                            {bar}
                            <div style="margin-top:1rem;font-size:0.8rem;color:#94a3b8;line-height:1.6;background:#080808;padding:1rem;border:1px solid #333;max-height:200px;overflow-y:auto;">
                                {body}
                            </div>
                            """, unsafe_allow_html=True)
                            
                    # ── Negative News Section ──
                    neg_articles = [
                        a for a in articles if a.get("is_negative_news", False)
                    ]
                    neg_count = len(neg_articles)
                    
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;margin:2rem 0 1rem;">
                        <div style="font-family:'Fira Code',monospace;font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#f59e0b;">⚠️ RECENT NEGATIVE NEWS FOR {entity['resolved_name'].upper()}</div>
                        <div style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#fcd34d;"
                        >{neg_count} ARTICLE{'S' if neg_count != 1 else ''} FLAGGED</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if neg_count == 0:
                        st.markdown("""
                        <div style='font-family:"Fira Code",monospace;font-size:0.8rem;
                             color:#4ade80;padding:0.75rem 1rem;
                             background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);
                             border-radius:8px;'>
                            ✔ No recent negative news detected for this entity.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        for neg_art in neg_articles:
                            sev_n   = neg_art.get("severity_label", "LOW").upper()
                            title_n = neg_art.get("article_title", "Untitled")
                            src_n   = neg_art.get("source", "")
                            date_n  = (neg_art.get("published_date") or "")[:10] or "Unknown date"
                            body_n  = neg_art.get("article_text", "")
                            sent_n  = neg_art.get("sentiment_score", 0.0)
                            sent_pct = min(100, sent_n * 100)
                            
                            # Sentiment bar colour: green=low, amber=mid, red=high
                            if sent_n >= 0.70:
                                sent_clr = "#ef4444"
                                sent_lbl = "HIGH NEGATIVE"
                            elif sent_n >= 0.45:
                                sent_clr = "#f59e0b"
                                sent_lbl = "MODERATE NEGATIVE"
                            else:
                                sent_clr = "#fcd34d"
                                sent_lbl = "LOW NEGATIVE"
                            
                            with st.expander(
                                f"⚠️ {sev_n} | SENTIMENT: {sent_pct:.0f}% | {title_n}",
                                expanded=False,
                            ):
                                st.markdown(f"""
                                <div style="margin-bottom:0.8rem;font-family:'Fira Code',monospace;font-size:0.75rem;color:#fca5a5;">
                                    DATE: <span style="color:#f8fafc;">{date_n}</span>
                                    &nbsp;|&nbsp;
                                    SOURCE: <a href="{src_n}" target="_blank"
                                        style="color:#fcd34d;text-decoration:none;">{src_n[:80]}</a>
                                </div>
                                <div style="margin-bottom:0.6rem;">
                                    {sev_badge(sev_n)}
                                    &nbsp;
                                    <span class="badge" style="background:rgba(245,158,11,0.15);
                                        color:#fcd34d;border:1px solid rgba(245,158,11,0.4);">
                                        NEGATIVE NEWS
                                    </span>
                                </div>
                                <div style="margin-bottom:0.5rem;font-family:'Fira Code',monospace;font-size:0.7rem;color:#f59e0b;">
                                    SENTIMENT WEIGHT
                                </div>
                                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                                    <div style="flex:1;background:#000;border:1px solid #333;height:8px;border-radius:4px;">
                                        <div style="width:{sent_pct:.1f}%;height:100%;background:{sent_clr};border-radius:4px;"></div>
                                    </div>
                                    <span style="font-family:'Fira Code',monospace;font-size:0.75rem;
                                        color:{sent_clr};min-width:5rem;">
                                        {sent_n:.2f} — {sent_lbl}
                                    </span>
                                </div>
                                <div style="font-size:0.8rem;color:#94a3b8;line-height:1.6;
                                    background:#080808;padding:1rem;border:1px solid #333;
                                    max-height:180px;overflow-y:auto;">
                                    {body_n[:600]}{'...' if len(body_n) > 600 else ''}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin:2rem 0;'>", unsafe_allow_html=True)
                    
                    # ── Human in the Loop ──
                    st.markdown("""<div class="ss-card-title-green" style="margin-top:2rem;">HUMAN-IN-THE-LOOP DECISION</div>""", unsafe_allow_html=True)
                    notes = st.text_area("ANALYST NOTES", placeholder="Document reasoning for decision...", height=100, key="analyst_notes")
                    
                    b1, b2, b3 = st.columns(3)
                    audit_base = {
                        "screening_id": data["screening_id"],
                        "entity_name":  entity["resolved_name"],
                        "analyst_notes": notes,
                        "risk_score":   risk_score,
                        "risk_category": risk_cat,
                    }
                    
                    # Customizing the APPROVE button explicitly inside markdown wrapper
                    with b1:
                        if st.button("✅ APPROVE (FALSE POSITIVE)", use_container_width=True):
                            requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "APPROVE"})
                            st.success("LOGGED: APPROVED")
                    with b2:
                        if st.button("⚠️ Escalate", use_container_width=True):
                            requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "ESCALATE"})
                            st.warning("This has been escalated")
                    with b3:
                        if st.button("❌ REJECT / BLOCK", type="primary", use_container_width=True):
                            requests.post(f"{API_BASE}/audit", json={**audit_base, "action": "REJECT"})
                            st.error("LOGGED: REJECTED")

            except Exception as e:
                st.error(f"SYSTEM FAILURE: {e}")

# ==============================================================================
# TAB: AUDIT LOGS
# ==============================================================================
with tab_audit:
    st.markdown("""<div class="ss-card-title">AUDIT LOG REGISTRY</div>""", unsafe_allow_html=True)
    if st.button("🔄 REFRESH LOGS"):
        pass
    
    try:
        logs = requests.get(f"{API_BASE}/audit-log", timeout=5).json()
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                    "risk_score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
                }
            )
        else:
            st.markdown("<div style='color:#6b2121;font-family:\"Fira Code\",monospace;'>[NO AUDIT LOGS FOUND]</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"COULD NOT FETCH LOGS: {e}")


# ==============================================================================
# TAB: COMPLIANCE DATABASE
# ==============================================================================
with tab_comp:
    st.markdown("""<div class="ss-card-title">COMPLIANCE DATA WAREHOUSE</div>""", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        f_entity = st.text_input("FILTER BY ENTITY", key="db_entity")
    with c2:
        f_sev = st.selectbox("FILTER BY SEVERITY", ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"], key="db_sev")
    with c3:
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        if st.button("QUERY DATABASE ➜", type="primary", use_container_width=True):
            pass
            
    try:
        params = {"limit": 100}
        if f_entity: params["entity"] = f_entity
        if f_sev != "ALL": params["severity"] = f_sev.lower()
        
        arts = requests.get(f"{API_BASE}/articles", params=params, timeout=5).json()
        if arts:
            df = pd.DataFrame(arts)
            # Display important columns
            cols = ["entity_name", "severity_label", "category", "published_date", "article_title"]
            available_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, height=500)
        else:
            st.markdown("<div style='color:#6b2121;font-family:\"Fira Code\",monospace;'>[NO RECORDS FOUND MATCHING CRITERIA]</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"DATABASE CONNECTION ERROR: {e}")


# ==============================================================================
# TAB: ROCm GPU DIAGNOSTICS
# ==============================================================================
with tab_rocm:
    st.markdown("""<div class="ss-card-title-green">SYSTEM HEALTH & GPU TELEMETRY (AUTO-REFRESHING)</div>""", unsafe_allow_html=True)
    
    @st.cache_data(ttl=60)
    def fetch_cached_health():
        return requests.get(f"{API_BASE}/health", timeout=5).json()

    @st.cache_data(ttl=60)
    def fetch_cached_stats():
        return requests.get(f"{API_BASE}/dataset-stats", timeout=5).json()

    @st.fragment(run_every="1s")
    def render_rocm_telemetry():
        try:
            health = fetch_cached_health()
            tel = requests.get(f"{API_BASE}/telemetry", timeout=5).json()
            stats = fetch_cached_stats()
            
            st.session_state.vram_usage = tel.get("vram_usage", st.session_state.vram_usage)
            st.session_state.compute_load = tel.get("compute_load", st.session_state.compute_load)
            
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("API STATUS", health.get("status", "UNKNOWN").upper())
            r2.metric("COMPUTE NODE", health.get("device_name", "UNKNOWN"))
            r3.metric("MODEL LOADED", "YES" if health.get("model_loaded") else "NO")
            r4.metric("DATASET SIZE", f"{stats.get('total_articles', 0):,}")
            
            st.markdown("<hr style='border-color:rgba(34,197,94,0.15); margin:2rem 0;'>", unsafe_allow_html=True)
            
            # Simulated GPU Dashboard
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f"""
                <div class="ss-card" style="border-color: rgba(34,197,94,0.3);">
                    <div class="ss-card-title-green">VRAM ALLOCATION (MiB)</div>
                    <div style="font-family:'Fira Code',monospace;font-size:2.5rem;color:#f8fafc;font-weight:800;margin-bottom:1rem;">
                        {st.session_state.vram_usage} <span style="font-size:1rem;color:#16a34a;">/ 198000</span>
                    </div>
                    <div style="background:#000;border:1px solid #333;height:12px;">
                        <div style="width:{min(100, st.session_state.vram_usage/198000*100):.1f}%;height:100%;background:#22c55e;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_g2:
                st.markdown(f"""
                <div class="ss-card" style="border-color: rgba(34,197,94,0.3);">
                    <div class="ss-card-title-green">COMPUTE ENGINE LOAD</div>
                    <div style="font-family:'Fira Code',monospace;font-size:2.5rem;color:#f8fafc;font-weight:800;margin-bottom:1rem;">
                        {st.session_state.compute_load}%
                    </div>
                    <div style="background:#000;border:1px solid #333;height:12px;">
                        <div style="width:{st.session_state.compute_load}%;height:100%;background:#22c55e;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown(f"""
            <div class="ss-card" style="border-color: rgba(34,197,94,0.3);">
                <div class="ss-card-title-green">DRIVER INFORMATION</div>
                <pre style="background:#000;border:1px solid #333;color:#4ade80;padding:1rem;font-family:'Fira Code',monospace;font-size:0.8rem;border-radius:4px;">
Node: {health.get('device', 'cuda:0')}
Architecture: CDNA 2
Driver Version: 5.4.3
HIP Runtime: 5.4.22804
System RAM: 256 GB
PyTorch Version: 2.1.0+rocm5.4.2
FastAPI Backend: v{health.get('version', '1.0')}
                </pre>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"TELEMETRY OFFLINE: {e}")

    render_rocm_telemetry()
