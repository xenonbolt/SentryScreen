"""
relevance_scorer.py — Relevance Scoring Agent
===============================================
Enriches retrieved articles with normalised relevance scores and
recency decay factors. Filters articles below the threshold.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.config import RECENCY_HALF_LIFE_DAYS, RELEVANCE_THRESHOLD

logger = logging.getLogger(__name__)


def _recency_factor(date_str: str, half_life: int = RECENCY_HALF_LIFE_DAYS) -> float:
    """
    Exponential decay: returns 1.0 for today, 0.5 after `half_life` days.

    f(t) = exp(−ln2 · t / half_life)
    """
    try:
        pub = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            pub = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return 0.50   # neutral fallback

    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)

    days_ago = (datetime.now(timezone.utc) - pub).days
    days_ago = max(0, days_ago)
    factor = math.exp(-math.log(2) * days_ago / half_life)
    return round(max(0.01, min(1.0, factor)), 4)


def score_articles(
    retrieved: List[Tuple[Dict[str, Any], float]],
    threshold: float = RELEVANCE_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Apply relevance scoring to the retrieval results.

    1. Filter articles below the similarity threshold.
    2. Compute recency factor from published_date.
    3. Normalise relevance scores to [0, 1] relative to the top article.

    Args:
        retrieved:  Output of MediaRetrievalAgent.retrieve() — list of
                    (article_dict, raw_similarity_score).
        threshold:  Minimum score to include.

    Returns:
        List of article dicts enriched with:
          - relevance_score           (raw cosine similarity)
          - relevance_score_normalized (relative to top result)
          - recency_factor            (exponential decay)
    """
    scored: List[Dict[str, Any]] = []

    for article, sim in retrieved:
        if sim < threshold:
            continue
        rf = _recency_factor(article.get("published_date", "2020-01-01"))
        scored.append({
            **article,
            "relevance_score": round(sim, 6),
            "recency_factor":  rf,
        })

    if not scored:
        logger.info("[RelevanceScorer] No articles passed threshold.")
        return []

    # Normalise
    max_sim = max(a["relevance_score"] for a in scored)
    denom   = max_sim if max_sim > 0 else 1.0
    for a in scored:
        a["relevance_score_normalized"] = round(a["relevance_score"] / denom, 4)

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    logger.info(
        f"[RelevanceScorer] {len(scored)} articles scored "
        f"(top score={scored[0]['relevance_score']:.4f})"
    )
    return scored
