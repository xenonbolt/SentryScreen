"""
decision.py — Decision Agent
==============================
Aggregates all upstream agent outputs into the final ScreeningResponse,
computes the overall confidence score, and manages the audit log.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config import AUDIT_LOG_FILE, DEVICE
from app.models.schemas import (
    ArticleResult, ExplainabilityReport, ResolvedEntity,
    RiskBreakdown, RiskCategory, ScreeningResponse, SeverityLabel,
)

logger = logging.getLogger(__name__)


# ── Confidence Computation ────────────────────────────────────────────────────

def _confidence(
    risk_score: float,
    articles: List[Dict[str, Any]],
    entity_conf: float,
) -> float:
    """
    Overall confidence = blend of:
      - Entity resolution confidence (how sure we are about the name match)
      - Average article relevance score
      - Article count factor (more evidence → higher confidence)
    """
    if not articles:
        return round(entity_conf * 0.5, 3)

    avg_rel   = sum(a.get("relevance_score", 0.0) for a in articles) / len(articles)
    count_fac = min(1.0, len(articles) / 10.0)

    conf = (
        0.40 * entity_conf
        + 0.40 * avg_rel
        + 0.20 * count_fac
    )
    return round(min(1.0, max(0.0, conf)), 3)


# ── Mapping helpers ───────────────────────────────────────────────────────────

def _to_article_result(art: Dict[str, Any]) -> ArticleResult:
    try:
        sev = SeverityLabel(art.get("severity_label", "medium").lower())
    except ValueError:
        sev = SeverityLabel.MEDIUM

    return ArticleResult(
        id=art.get("id", str(uuid.uuid4())),
        entity_name=art.get("entity_name", ""),
        article_title=art.get("article_title", ""),
        article_text=art.get("article_text", ""),
        source=art.get("source", ""),
        published_date=art.get("published_date", ""),
        category=art.get("category", "unknown"),
        severity_label=sev,
        country=art.get("country", ""),
        relevance_score=round(float(art.get("relevance_score", 0.0)), 4),
        risk_contribution=round(float(art.get("risk_contribution", 0.0)), 2),
        keywords=art.get("keywords", []),
        why_flagged=art.get("why_flagged", ""),
        relevance_reason=art.get("relevance_reason", ""),
    )


# ── Main Decision Function ────────────────────────────────────────────────────

def make_decision(
    resolved_entity: ResolvedEntity,
    enriched_articles: List[Dict[str, Any]],
    risk_score: float,
    risk_category: RiskCategory,
    risk_breakdown: RiskBreakdown,
    explainability_report: ExplainabilityReport,
    start_time: float,
) -> ScreeningResponse:
    """
    Assemble the final ScreeningResponse from all agent outputs.

    Args:
        resolved_entity:     Output of EntityResolverAgent.
        enriched_articles:   Output of ExplainabilityAgent (fully decorated).
        risk_score:          Aggregate risk score 0–100.
        risk_category:       LOW / MEDIUM / HIGH.
        risk_breakdown:      Per-component breakdown of the risk score.
        explainability_report: Full explainability report.
        start_time:          time.perf_counter() at request start.

    Returns:
        ScreeningResponse
    """
    screening_id = str(uuid.uuid4())
    conf         = _confidence(risk_score, enriched_articles, resolved_entity.confidence)
    article_objs = [_to_article_result(a) for a in enriched_articles]
    elapsed_ms   = round((time.perf_counter() - start_time) * 1000, 2)

    response = ScreeningResponse(
        screening_id=screening_id,
        entity=resolved_entity,
        articles=article_objs,
        risk_score=risk_score,
        risk_category=risk_category,
        confidence_score=conf,
        risk_breakdown=risk_breakdown,
        explainability=explainability_report,
        total_articles_found=len(article_objs),
        device_used=DEVICE,
        processing_time_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc),
    )

    logger.info(
        f"[Decision] screening_id={screening_id} | "
        f"entity='{resolved_entity.resolved_name}' | "
        f"risk={risk_score:.1f} ({risk_category.value}) | "
        f"conf={conf:.3f} | articles={len(article_objs)} | "
        f"elapsed={elapsed_ms:.0f}ms"
    )
    return response


# ── Audit Log I/O ─────────────────────────────────────────────────────────────

def append_audit_entry(entry: Dict[str, Any]) -> None:
    """Append a single audit log entry (JSONL format)."""
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
        logger.info(
            f"[AuditLog] Entry written: action={entry.get('action')} "
            f"for screening_id={entry.get('screening_id')}"
        )
    except Exception as exc:
        logger.error(f"[AuditLog] Failed to write entry: {exc}")


def read_audit_entries(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent `limit` audit log entries."""
    entries: List[Dict[str, Any]] = []
    try:
        if not AUDIT_LOG_FILE.exists():
            return entries
        with open(AUDIT_LOG_FILE, encoding="utf-8") as fh:
            lines = fh.readlines()
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as exc:
        logger.error(f"[AuditLog] Failed to read: {exc}")
    return entries
