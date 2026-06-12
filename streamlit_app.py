import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Adverse Media Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL (Ensure FastAPI is running on port 8000)
API_BASE = "http://localhost:8000/api"

# Custom CSS for UI polish
st.markdown("""
<style>
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-med { color: #faca2b; font-weight: bold; }
    .risk-low { color: #00cc96; font-weight: bold; }
    .metric-card {
        background-color: #1e1e2e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: System Info ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ SentryScreen")
    st.caption("Adverse Media Copilot")
    
    st.divider()
    if st.button("🔄 Refresh Backend Status"):
        try:
            health = requests.get(f"{API_BASE}/health").json()
            stats = requests.get(f"{API_BASE}/dataset-stats").json()
            st.success("Backend Connected")
            st.write(f"**Device:** {health['device']} ({health['device_name']})")
            st.write(f"**Dataset:** {stats['total_articles']} Articles")
            st.write(f"**Entities:** {stats['unique_entities']}")
        except Exception as e:
            st.error("Backend Offline. Ensure FastAPI is running on port 8000.")

# ── Main Interface ────────────────────────────────────────────────────────────
st.title("Entity Screening")

query = st.text_input("Enter Company or Person Name", placeholder="e.g., Nexum Capital Partners", key="search_query")

if st.button("Screen Entity", type="primary") and query:
    with st.spinner("Screening entity across vector database..."):
        try:
            res = requests.post(f"{API_BASE}/screen", json={"entity_name": query, "top_k": 10, "threshold": 0.15})
            
            if res.status_code == 200:
                data = res.json()
                
                # Top Level Metrics
                st.subheader("Assessment Results")
                col1, col2, col3, col4 = st.columns(4)
                
                risk_cat = data['risk_category']
                cat_color = "🔴" if risk_cat == "HIGH" else "🟡" if risk_cat == "MEDIUM" else "🟢"
                
                col1.metric("Risk Score", f"{data['risk_score']:.1f}/100", f"{cat_color} {risk_cat}", delta_color="off")
                col2.metric("Confidence", f"{(data['confidence_score'] * 100):.1f}%")
                col3.metric("Articles Flagged", data['total_articles_found'])
                col4.metric("Entity Resolved As", data['entity']['resolved_name'])

                st.divider()

                # Explainability Panel
                st.subheader("Executive Summary")
                st.info(data['explainability']['summary'])
                
                colA, colB = st.columns(2)
                with colA:
                    st.markdown("**Key Risk Factors:**")
                    for factor in data['explainability']['key_risk_factors']:
                        st.write(factor)
                with colB:
                    st.markdown("**Top Keywords:**")
                    st.write(", ".join(data['explainability']['top_keywords']))

                st.divider()

                # Articles Table
                st.subheader("Adverse Media Findings")
                if data['articles']:
                    # Convert to dataframe for clean display
                    df = pd.DataFrame(data['articles'])
                    display_df = df[['severity_label', 'category', 'published_date', 'article_title', 'source', 'relevance_score']].copy()
                    display_df['severity_label'] = display_df['severity_label'].str.upper()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Detailed Expanders
                    st.markdown("### Article Details")
                    for art in data['articles']:
                        with st.expander(f"{art['severity_label'].upper()} | {art['article_title']} ({art['published_date']})"):
                            st.write(f"**Source:** {art['source']} | **Category:** {art['category']}")
                            st.markdown(f"> **Why Flagged:** {art['why_flagged']}")
                            st.write(art['article_text'])
                else:
                    st.success("No adverse media findings above threshold.")

                st.divider()

                # Human Review Actions
                st.subheader("Human-in-the-Loop Review")
                notes = st.text_area("Analyst Notes (Optional)")
                r_col1, r_col2, r_col3 = st.columns(3)
                
                if r_col1.button("✅ Approve / False Positive", use_container_width=True):
                    requests.post(f"{API_BASE}/audit", json={"screening_id": data['screening_id'], "entity_name": data['entity']['resolved_name'], "action": "APPROVE", "analyst_notes": notes, "risk_score": data['risk_score'], "risk_category": data['risk_category']})
                    st.success("Audit log updated: APPROVED")
                
                if r_col2.button("⚠️ Escalate to EDD", use_container_width=True):
                    requests.post(f"{API_BASE}/audit", json={"screening_id": data['screening_id'], "entity_name": data['entity']['resolved_name'], "action": "ESCALATE", "analyst_notes": notes, "risk_score": data['risk_score'], "risk_category": data['risk_category']})
                    st.warning("Audit log updated: ESCALATED")
                
                if r_col3.button("❌ Reject / Block", use_container_width=True):
                    requests.post(f"{API_BASE}/audit", json={"screening_id": data['screening_id'], "entity_name": data['entity']['resolved_name'], "action": "REJECT", "analyst_notes": notes, "risk_score": data['risk_score'], "risk_category": data['risk_category']})
                    st.error("Audit log updated: REJECTED")

            else:
                st.error(f"Backend Error: {res.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend. Is FastAPI running? ({e})")
