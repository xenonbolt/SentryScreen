"""
risk_analyst.py — Risk Analysis Agent
=======================================
Applies the weighted risk-scoring formula to compute per-article
contribution scores and an aggregate entity risk score (0–100).

Formula (v2 — with sentiment dimension):
    article_risk = (
        0.30 × relevance_score_normalized
      + 0.22 × severity_weight
      + 0.20 × frequency_factor
      + 0.13 × recency_factor
      + 0.15 × sentiment_weight          ← NEW
    ) × 100

Sentiment weight is computed via a two-tier approach:
  1. Zero-Shot Classification (ZSC) using a distilled NLI model
     (cross-encoder/nli-deberta-v3-small) — acts as the primary "labeler"
     without requiring any labelled training data.
  2. Keyword cluster fallback — augments or replaces ZSC when the model
     is unavailable or when keyword signals are very strong.

Aggregate risk uses an inverse-rank-weighted average of per-article
scores, biased toward the most severe findings.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from app.config import (
    SEVERITY_WEIGHTS, SENTIMENT_KEYWORDS,
    WEIGHT_FREQUENCY, WEIGHT_RECENCY,
    WEIGHT_RELEVANCE, WEIGHT_SEVERITY, WEIGHT_SENTIMENT,
    RISK_THRESHOLDS,
    ZSC_ENABLED, ZSC_MODEL, ZSC_NEGATIVE_LABEL,
    ZSC_POSITIVE_LABEL, ZSC_THRESHOLD,
)
from app.models.schemas import RiskBreakdown, RiskCategory

logger = logging.getLogger(__name__)

# ── ZSC model singleton (lazy-loaded) ────────────────────────────────────────
_zsc_pipeline: Optional[Any] = None
_zsc_load_attempted: bool = False


def _get_zsc_pipeline() -> Optional[Any]:
    """
    Lazy-load the zero-shot classification pipeline once.
    Returns None gracefully if transformers is unavailable or model fails to load.
    Uses cross-encoder/nli-deberta-v3-small (~184 MB) — fast on CPU, ~50 ms/article.
    """
    global _zsc_pipeline, _zsc_load_attempted
    if _zsc_load_attempted:
        return _zsc_pipeline
    _zsc_load_attempted = True

    if not ZSC_ENABLED:
        logger.info("[RiskAnalyst] ZSC disabled via config.")
        return None

    try:
        from transformers import pipeline
        logger.info(f"[RiskAnalyst] Loading ZSC pipeline: '{ZSC_MODEL}'")
        _zsc_pipeline = pipeline(
            "zero-shot-classification",
            model=ZSC_MODEL,
            # Use CPU for ZSC to leave GPU for embedding model
            device=-1,
        )
        logger.info("[RiskAnalyst] ZSC pipeline ready.")
    except Exception as exc:
        logger.warning(f"[RiskAnalyst] ZSC pipeline unavailable — falling back to keywords only: {exc}")
        _zsc_pipeline = None

    return _zsc_pipeline


# ── Helpers ───────────────────────────────────────────────────────────────────

def _severity_weight(label: str) -> float:
    return SEVERITY_WEIGHTS.get(label.lower(), 0.50)


def _frequency_factor(n_articles: int, saturation: int = 50) -> float:
    """Log-normalised: 0 → 0.0, 10 → ~0.48, 50 → 1.0."""
    if n_articles == 0:
        return 0.0
    return round(min(1.0, math.log1p(n_articles) / math.log1p(saturation)), 4)


def _classify(score: float) -> RiskCategory:
    for cat, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= score <= hi:
            return RiskCategory(cat)
    return RiskCategory.HIGH


def _keyword_sentiment(text: str) -> float:
    """
    Scan title + article text for sentiment keyword clusters.
    Returns a raw sentiment weight in [−0.30, 1.00].
    Multiple keyword hits are averaged (not summed) to avoid over-counting.
    """
    text_lower = text.lower()
    hits: List[float] = []

    for keyword, weight in SENTIMENT_KEYWORDS.items():
        if keyword in text_lower:
            hits.append(weight)

    if not hits:
        return 0.0

    # Average of matched weights — dampens multi-hit over-inflation
    raw = sum(hits) / len(hits)
    return raw


def _zsc_sentiment(text: str, is_negative_hint: bool) -> Optional[float]:
    """
    Run zero-shot classification to determine negative sentiment probability.

    Labels:
      - ZSC_NEGATIVE_LABEL: "negative news about a company or person"
      - ZSC_POSITIVE_LABEL: "positive or neutral news about a company or person"

    Returns the score for the negative label [0.0, 1.0], or None on failure.
    The `is_negative_hint` (True when article came from the adverse query)
    is used as a soft prior — if ZSC is uncertain (near 0.5), the hint
    breaks the tie.
    """
    zsc = _get_zsc_pipeline()
    if zsc is None:
        return None

    try:
        # Truncate to first 512 chars — NLI models have token limits
        snippet = text[:512]
        result = zsc(
            snippet,
            candidate_labels=[ZSC_NEGATIVE_LABEL, ZSC_POSITIVE_LABEL],
        )
        # result["labels"][0] is the top-ranked label
        label_scores: Dict[str, float] = dict(
            zip(result["labels"], result["scores"])
        )
        neg_score = label_scores.get(ZSC_NEGATIVE_LABEL, 0.0)

        # Apply soft prior from query hint: nudge ±0.10 if ZSC is uncertain
        if abs(neg_score - 0.5) < 0.15:
            neg_score = neg_score + (0.10 if is_negative_hint else -0.05)
            neg_score = max(0.0, min(1.0, neg_score))

        return round(neg_score, 4)

    except Exception as exc:
        logger.debug(f"[RiskAnalyst] ZSC inference failed: {exc}")
        return None


def _compute_sentiment_weight(article: Dict[str, Any]) -> float:
    """
    Hybrid sentiment scoring:
      1. ZSC score (primary — if available and above threshold)
      2. Keyword cluster score (always computed as augmentation / fallback)
      3. Blend: 0.65 × ZSC + 0.35 × keyword (if both available)
         OR pure keyword if ZSC unavailable.

    Additionally, articles explicitly tagged is_negative_news=True get a
    small floor boost (min 0.40) since they were retrieved via the adverse query.

    Final result is clamped to [0.0, 1.0].
    """
    text = (
        article.get("article_title", "")
        + " "
        + article.get("article_text", "")[:600]
    )
    is_negative_hint = article.get("is_negative_news", False)

    kw_score  = _keyword_sentiment(text)
    zsc_score = _zsc_sentiment(text, is_negative_hint)

    if zsc_score is not None:
        # Blend ZSC (primary) + keyword (augment)
        blended = 0.65 * zsc_score + 0.35 * kw_score
    else:
        # Keyword-only fallback
        blended = kw_score

    # Floor for articles explicitly from adverse search
    if is_negative_hint:
        blended = max(blended, 0.40)

    return round(min(1.0, max(0.0, blended)), 4)


# ── Main Agent Function ───────────────────────────────────────────────────────

def analyze_risk(
    scored_articles: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], float, RiskCategory, RiskBreakdown]:
    """
    Compute per-article and aggregate risk scores.

    Args:
        scored_articles: Output of RelevanceScoringAgent — list of article
                         dicts that include relevance_score_normalized and
                         recency_factor.

    Returns:
        (enriched_articles, aggregate_risk_score, risk_category, breakdown)
    """
    if not scored_articles:
        logger.info("[RiskAnalyst] No articles — returning zero risk.")
        breakdown = RiskBreakdown(
            relevance_component=0.0,
            severity_component=0.0,
            frequency_component=0.0,
            recency_component=0.0,
            sentiment_component=0.0,
            negative_news_count=0,
        )
        return [], 0.0, RiskCategory.LOW, breakdown

    n = len(scored_articles)
    freq_factor = _frequency_factor(n)
    enriched: List[Dict[str, Any]] = []

    # Pre-load ZSC once (lazy singleton)
    _get_zsc_pipeline()

    for art in scored_articles:
        rel  = art.get("relevance_score_normalized", art.get("relevance_score", 0.0))
        rec  = art.get("recency_factor", 0.50)
        sent = _compute_sentiment_weight(art)

        # ── DYNAMIC FALSE POSITIVE MITIGATION ──
        # Live web searches blindly assign HIGH severity to any hit from an adverse query.
        # If NLP sentiment analysis strongly disagrees (score hits the 0.40 floor),
        # it is a benign article (e.g. Wikipedia) that ranked high on DuckDuckGo. Downgrade it.
        sev_label = art.get("severity_label", "medium")
        if art.get("is_negative_news") and sent <= 0.45:
            sev_label = "low"
            art["severity_label"] = "low"
            art["category"] = "GENERAL_NEWS"
            art["is_negative_news"] = False
            
        sev  = _severity_weight(sev_label)

        # ── BENIGN DAMPENING ──
        # If an article is purely benign (low severity background info or general news),
        # its high relevance (being about the entity) and high recency (published today)
        # shouldn't trigger an 'Adverse' Media risk. We suppress its risk factors.
        if sev_label == "low":
            rel *= 0.25
            rec *= 0.25
            sent *= 0.0

        contribution = (
            WEIGHT_RELEVANCE  * rel
            + WEIGHT_SEVERITY   * sev
            + WEIGHT_FREQUENCY  * freq_factor
            + WEIGHT_RECENCY    * rec
            + WEIGHT_SENTIMENT  * sent
        ) * 100.0

        contribution = round(min(100.0, max(0.0, contribution)), 2)
        
        # Write the dampened values back so the UI Breakdown bars match the math
        art["relevance_score_normalized"] = rel
        art["recency_factor"] = rec
        art["sentiment_score"] = sent
        enriched.append({
            **art,
            "sentiment_score":    sent,
            "is_negative_news":   art.get("is_negative_news", False),
            "risk_contribution":  contribution,
        })

    # Sort by contribution descending
    enriched.sort(key=lambda x: x["risk_contribution"], reverse=True)

    # Inverse-rank weighted aggregate
    weights = [1.0 / (i + 1) for i in range(len(enriched))]
    total_w = sum(weights)
    aggregate = sum(
        a["risk_contribution"] * w for a, w in zip(enriched, weights)
    ) / total_w

    # Severity-based penalty bonus (escalates score for critical findings)
    critical_n = sum(1 for a in enriched if a.get("severity_label") == "critical")
    high_n     = sum(1 for a in enriched if a.get("severity_label") == "high")
    bonus = min(12.0, critical_n * 4.0 + high_n * 1.5)
    aggregate = round(min(100.0, aggregate + bonus), 2)

    category = _classify(aggregate)

    # Negative news count
    negative_news_count = sum(1 for a in enriched if a.get("is_negative_news"))

    # Compute breakdown components (averaged across articles)
    avg_rel  = sum(
        a.get("relevance_score_normalized", a.get("relevance_score", 0)) for a in enriched
    ) / n
    avg_sev  = sum(_severity_weight(a.get("severity_label", "medium")) for a in enriched) / n
    avg_rec  = sum(a.get("recency_factor", 0.5) for a in enriched) / n
    avg_sent = sum(a.get("sentiment_score", 0.0) for a in enriched) / n

    breakdown = RiskBreakdown(
        relevance_component= round(WEIGHT_RELEVANCE  * avg_rel  * 100, 2),
        severity_component=  round(WEIGHT_SEVERITY   * avg_sev  * 100, 2),
        frequency_component= round(WEIGHT_FREQUENCY  * freq_factor * 100, 2),
        recency_component=   round(WEIGHT_RECENCY    * avg_rec  * 100, 2),
        sentiment_component= round(WEIGHT_SENTIMENT  * avg_sent * 100, 2),
        negative_news_count= negative_news_count,
    )

    logger.info(
        f"[RiskAnalyst] score={aggregate:.1f}, category={category.value}, "
        f"articles={n}, freq={freq_factor:.3f}, avg_sentiment={avg_sent:.3f}, "
        f"negative_news={negative_news_count}"
    )
    return enriched, aggregate, category, breakdown
