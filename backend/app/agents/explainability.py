"""
explainability.py — Explainability Agent
==========================================
Generates human-readable, structured explanations for why an entity
was flagged, why each article increases risk, and what keywords are
most significant. Optionally enhances summaries with a local Ollama LLM.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from app.config import OLLAMA_BASE_URL, OLLAMA_ENABLED, OLLAMA_MODEL
from app.models.schemas import ExplainabilityReport, RiskCategory

logger = logging.getLogger(__name__)


# ── Category narratives ───────────────────────────────────────────────────────
_CAT_NARRATIVE: Dict[str, str] = {
    "fraud":                "fraudulent financial activity and misrepresentation",
    "money_laundering":     "money laundering of criminal proceeds",
    "sanctions":            "sanctions violations and dealings with restricted entities",
    "bribery":              "bribery and public corruption",
    "tax_evasion":          "offshore tax evasion and financial concealment",
    "cybercrime":           "cybercrime, data breaches, and digital espionage",
    "environmental":        "environmental law violations and ecological damage",
    "human_rights":         "human rights and forced labour violations",
    "terrorism_financing":  "terrorism financing and support for proscribed groups",
    "regulatory":           "regulatory non-compliance and licence violations",
    "insider_trading":      "insider trading and market manipulation",
}

# Weighted risk keywords for extraction
_RISK_KEYWORDS: List[str] = [
    "fraud", "fraudulent", "corrupt", "corruption", "sanction", "sanctioned",
    "bribe", "bribery", "launder", "laundering", "investigation", "arrested",
    "convicted", "indicted", "charged", "penalty", "fine", "fined",
    "violation", "illegal", "criminal", "banned", "prohibited",
    "tax evasion", "embezzle", "embezzlement", "scam", "ponzi", "forgery",
    "trafficking", "terrorist", "terrorism", "breach", "misconduct",
    "whistleblower", "offshore", "shell company", "hack", "exploit",
    "seizure", "frozen", "asset freeze", "money mule", "proceeds",
    "designated", "blacklisted", "debarred",
]


# ── Keyword extractor ─────────────────────────────────────────────────────────

def _extract_keywords(text: str, top_n: int = 8) -> List[str]:
    """
    Extract risk-relevant keywords from article text.
    Uses pattern matching; upgrades to KeyBERT if available.
    """
    text_lower = text.lower()
    found: List[str] = []
    seen: set[str] = set()

    for kw in _RISK_KEYWORDS:
        if kw in text_lower:
            # Grab a short surrounding phrase
            pattern = rf'\b[\w\s]{{0,6}}{re.escape(kw)}[\w\s]{{0,6}}\b'
            for m in re.finditer(pattern, text_lower):
                phrase = m.group().strip()
                if phrase not in seen and len(phrase) > 3:
                    seen.add(phrase)
                    found.append(phrase)
                    break

    # KeyBERT upgrade (optional)
    try:
        from keybert import KeyBERT
        kbm = KeyBERT()
        bert_kws = kbm.extract_keywords(
            text, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5
        )
        for kw, _ in bert_kws:
            if kw not in seen:
                seen.add(kw)
                found.append(kw)
    except Exception:
        pass   # KeyBERT not installed or failed — silently skip

    return found[:top_n]


# ── Per-article explanations ──────────────────────────────────────────────────

def _relevance_reason(article: Dict[str, Any], entity_name: str) -> str:
    cat       = article.get("category", "unknown")
    severity  = article.get("severity_label", "medium")
    source    = article.get("source", "an unspecified source")
    date      = article.get("published_date", "unknown date")[:10]
    narrative = _CAT_NARRATIVE.get(cat, f"{cat.replace('_', ' ')} risk")

    severity_desc = {
        "critical": "critical regulatory and reputational exposure",
        "high":     "significant risk factors requiring immediate attention",
        "medium":   "moderate risk indicators warranting enhanced due diligence",
        "low":      "low-level risk indicators for monitoring",
    }.get(severity, "elevated risk indicators")

    return (
        f"Reported by {source} on {date}, this article directly associates '{entity_name}' "
        f"with {narrative}. Severity is assessed as {severity.upper()}, "
        f"indicating {severity_desc}."
    )


def _why_flagged(article: Dict[str, Any]) -> str:
    cat       = article.get("category", "unknown").replace("_", " ")
    severity  = article.get("severity_label", "medium").upper()
    relevance = article.get("relevance_score", 0.0)
    contrib   = article.get("risk_contribution", 0.0)

    return (
        f"Flagged: {severity} severity {cat} content detected. "
        f"Semantic relevance score: {relevance:.2f}. "
        f"Contributes {contrib:.1f} points to the aggregate risk score. "
        f"Article content closely matches the entity's risk profile."
    )


# ── Deterministic summary ─────────────────────────────────────────────────────

def _deterministic_summary(
    entity_name: str,
    articles: List[Dict[str, Any]],
    risk_score: float,
    risk_category: RiskCategory,
) -> str:
    if not articles:
        return (
            f"No adverse media found for '{entity_name}'. "
            f"Based on the available dataset, this entity presents a LOW risk profile."
        )

    cat_counts = Counter(a.get("category", "unknown") for a in articles)
    top_cats   = ", ".join(
        f"{c.replace('_', ' ')} ({n})"
        for c, n in cat_counts.most_common(3)
    )
    crit_n = sum(1 for a in articles if a.get("severity_label") == "critical")
    high_n = sum(1 for a in articles if a.get("severity_label") == "high")

    severity_note = ""
    if crit_n:
        severity_note = f" {crit_n} CRITICAL severity finding(s) identified."
    elif high_n:
        severity_note = f" {high_n} HIGH severity finding(s) identified."

    dates = sorted(
        a.get("published_date", "")[:10]
        for a in articles if a.get("published_date")
    )
    date_span = (
        f" Media coverage spans {dates[0]} to {dates[-1]}."
        if len(dates) >= 2 else ""
    )

    return (
        f"Adverse media screening for '{entity_name}' identified {len(articles)} relevant "
        f"article(s) with a composite risk score of {risk_score:.1f}/100 "
        f"({risk_category.value} risk).{severity_note} "
        f"Primary risk categories: {top_cats}.{date_span} "
        f"Assessment based on semantic similarity analysis and weighted multi-factor scoring."
    )


# ── Optional Ollama summary ───────────────────────────────────────────────────

def _ollama_summary(
    entity_name: str,
    articles: List[Dict[str, Any]],
    risk_score: float,
) -> str:
    try:
        import httpx
        snippets = "\n".join(
            f"- [{a.get('category', '?')} / {a.get('severity_label', '?')}] "
            f"{a.get('article_title', 'N/A')} ({a.get('published_date', '')[:10]}): "
            f"{a.get('article_text', '')[:180]}…"
            for a in articles[:5]
        )
        prompt = (
            f"You are a senior AML/financial-crime compliance analyst.\n"
            f"Write a concise 3–4 sentence professional risk summary for '{entity_name}' "
            f"based on the adverse media below (composite risk score: {risk_score:.1f}/100).\n\n"
            f"{snippets}\n\nSummary:"
        )
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30.0,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "").strip()
            if text:
                return text
    except Exception as exc:
        logger.debug(f"[Explainability] Ollama unavailable: {exc}")
    return ""


# ── Main Agent Function ───────────────────────────────────────────────────────

def explain(
    entity_name: str,
    articles: List[Dict[str, Any]],
    risk_score: float,
    risk_category: RiskCategory,
) -> Tuple[List[Dict[str, Any]], ExplainabilityReport]:
    """
    Enrich each article with explainability fields and produce an overall report.

    Returns:
        (enriched_articles, ExplainabilityReport)
    """
    enriched: List[Dict[str, Any]] = []
    all_keywords: List[str] = []

    for art in articles:
        kws   = _extract_keywords(art.get("article_title", "") + " " + art.get("article_text", ""))
        all_keywords.extend(kws)
        enriched.append({
            **art,
            "keywords":        kws,
            "why_flagged":     _why_flagged(art),
            "relevance_reason": _relevance_reason(art, entity_name),
        })

    # Category distribution
    cat_dist: Dict[str, int] = dict(Counter(a.get("category", "unknown") for a in articles))

    # Top global keywords
    kw_counter  = Counter(all_keywords)
    top_keywords = [kw for kw, _ in kw_counter.most_common(12)]

    # Key risk factor bullets
    key_factors: List[str] = []
    if any(a.get("severity_label") == "critical" for a in articles):
        key_factors.append("⚠️  Critical-severity adverse media detected")
    if "sanctions" in cat_dist:
        key_factors.append("🚫  Sanctions-related exposure identified")
    if "terrorism_financing" in cat_dist:
        key_factors.append("🔴  Terrorism financing risk indicators present")
    if "money_laundering" in cat_dist:
        key_factors.append("💰  Money laundering allegations on record")
    if len(articles) >= 5:
        key_factors.append(f"📰  High volume of adverse media ({len(articles)} articles)")
    if not key_factors:
        key_factors = ["ℹ️  Adverse media detected with moderate risk indicators"]

    # Timeline narrative
    dates = sorted(
        a.get("published_date", "")[:10]
        for a in articles if a.get("published_date")
    )
    if len(dates) >= 2:
        is_recent = dates[-1] >= "2024-01-01"
        timeline_analysis = (
            f"Adverse media spans {dates[0]} to {dates[-1]}, "
            f"indicating {'ongoing and recent' if is_recent else 'historical'} risk exposure."
        )
    elif dates:
        timeline_analysis = f"Single adverse media event recorded on {dates[0]}."
    else:
        timeline_analysis = "No publication dates available for timeline analysis."

    # Confidence explanation
    avg_rel = sum(a.get("relevance_score", 0) for a in articles) / max(len(articles), 1)
    if avg_rel > 0.65:
        conf_exp = "High confidence: strong semantic match between entity query and flagged articles."
    elif avg_rel > 0.40:
        conf_exp = "Moderate confidence: reasonable match — some articles may be peripheral."
    else:
        conf_exp = "Lower confidence: moderate match — manual analyst review is recommended."

    # Generate summary
    summary = _deterministic_summary(entity_name, articles, risk_score, risk_category)
    if OLLAMA_ENABLED:
        llm_summary = _ollama_summary(entity_name, articles, risk_score)
        if llm_summary:
            summary = llm_summary
            logger.info("[Explainability] Using Ollama-generated summary.")

    report = ExplainabilityReport(
        summary=summary,
        key_risk_factors=key_factors,
        category_distribution=cat_dist,
        top_keywords=top_keywords,
        timeline_analysis=timeline_analysis,
        confidence_explanation=conf_exp,
    )

    logger.info(
        f"[Explainability] Report generated: {len(key_factors)} key factors, "
        f"{len(top_keywords)} keywords, {len(cat_dist)} categories."
    )
    return enriched, report
