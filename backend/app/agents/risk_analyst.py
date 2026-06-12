"""
risk_analyst.py — Risk Analysis Agent
=======================================
Applies the weighted risk-scoring formula to compute per-article
contribution scores and an aggregate entity risk score (0–100).

Formula:
    article_risk = (
        0.35 × relevance_score_normalized
      + 0.25 × severity_weight
      + 0.25 × frequency_factor
      + 0.15 × recency_factor
    ) × 100

Aggregate risk uses an inverse-rank-weighted average of per-article
scores, biased toward the most severe findings.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Tuple

from app.config import (
    SEVERITY_WEIGHTS, WEIGHT_FREQUENCY, WEIGHT_RECENCY,
    WEIGHT_RELEVANCE, WEIGHT_SEVERITY, RISK_THRESHOLDS,
)
from app.models.schemas import RiskBreakdown, RiskCategory

logger = logging.getLogger(__name__)


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
        )
        return [], 0.0, RiskCategory.LOW, breakdown

    n = len(scored_articles)
    freq_factor = _frequency_factor(n)
    enriched: List[Dict[str, Any]] = []

    for art in scored_articles:
        rel  = art.get("relevance_score_normalized", art.get("relevance_score", 0.0))
        sev  = _severity_weight(art.get("severity_label", "medium"))
        rec  = art.get("recency_factor", 0.50)

        contribution = (
            WEIGHT_RELEVANCE  * rel
            + WEIGHT_SEVERITY   * sev
            + WEIGHT_FREQUENCY  * freq_factor
            + WEIGHT_RECENCY    * rec
        ) * 100.0

        contribution = round(min(100.0, max(0.0, contribution)), 2)
        enriched.append({**art, "risk_contribution": contribution})

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

    # Compute breakdown components (averaged across articles)
    avg_rel = sum(
        a.get("relevance_score_normalized", a.get("relevance_score", 0)) for a in enriched
    ) / n
    avg_sev = sum(_severity_weight(a.get("severity_label", "medium")) for a in enriched) / n
    avg_rec = sum(a.get("recency_factor", 0.5) for a in enriched) / n

    breakdown = RiskBreakdown(
        relevance_component=round(WEIGHT_RELEVANCE  * avg_rel * 100, 2),
        severity_component= round(WEIGHT_SEVERITY   * avg_sev * 100, 2),
        frequency_component=round(WEIGHT_FREQUENCY  * freq_factor * 100, 2),
        recency_component=  round(WEIGHT_RECENCY    * avg_rec * 100, 2),
    )

    logger.info(
        f"[RiskAnalyst] score={aggregate:.1f}, category={category.value}, "
        f"articles={n}, freq={freq_factor:.3f}"
    )
    return enriched, aggregate, category, breakdown
