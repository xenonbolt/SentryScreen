"""
routes.py — FastAPI API Routes
================================
All HTTP endpoints for the Adverse Media Screening Copilot.
"""

from __future__ import annotations

import time
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from app.agents.decision import append_audit_entry, make_decision, read_audit_entries
from app.agents.entity_resolver import resolve_entity
from app.agents.explainability import explain
from app.agents.media_retrieval import media_retrieval_agent
from app.agents.relevance_scorer import score_articles
from app.agents.risk_analyst import analyze_risk
from app.config import DEVICE, DEVICE_NAME, API_VERSION
from app.models.schemas import (
    AuditRequest, DatasetStats, HealthResponse,
    ScreeningRequest, ScreeningResponse,
)

logger    = logging.getLogger(__name__)
router    = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """System health and readiness probe."""
    return HealthResponse(
        status="ok",
        device=DEVICE,
        device_name=DEVICE_NAME,
        model_loaded=media_retrieval_agent.is_initialized,
        dataset_size=media_retrieval_agent.dataset_size,
        version=API_VERSION,
    )


# ── Dataset Stats ─────────────────────────────────────────────────────────────

@router.get("/dataset-stats", response_model=DatasetStats, tags=["system"])
async def dataset_stats() -> DatasetStats:
    """Return summary statistics about the loaded dataset."""
    if not media_retrieval_agent.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not yet initialised. Retry in a moment.",
        )
    articles = media_retrieval_agent.articles
    dates    = sorted(
        a.get("published_date", "")[:10]
        for a in articles if a.get("published_date")
    )
    return DatasetStats(
        total_articles=len(articles),
        unique_entities=len({a["entity_name"] for a in articles}),
        category_counts=dict(Counter(a.get("category", "?") for a in articles)),
        severity_counts=dict(Counter(a.get("severity_label", "?") for a in articles)),
        date_range={
            "earliest": dates[0] if dates else "N/A",
            "latest":   dates[-1] if dates else "N/A",
        },
        countries=sorted({a.get("country", "?") for a in articles}),
    )


# ── Main Screening Endpoint ───────────────────────────────────────────────────

@router.post(
    "/screen",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
    tags=["screening"],
    summary="Screen an entity for adverse media",
)
async def screen_entity(request: ScreeningRequest) -> ScreeningResponse:
    """
    Full 6-agent adverse media screening pipeline.

    1. Entity Resolver      — disambiguate name
    2. Media Retrieval      — FAISS semantic search
    3. Relevance Scorer     — normalise + recency decay
    4. Risk Analyst         — weighted risk formula
    5. Explainability Agent — keywords, narratives, summary
    6. Decision Agent       — final verdict + audit trail
    """
    t0 = time.perf_counter()
    logger.info(f"[API] Screening request: entity='{request.entity_name}'")

    if not media_retrieval_agent.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval agent is still initialising. Please retry in a few seconds.",
        )

    # 1 — Entity Resolution
    resolved = resolve_entity(
        query_name=request.entity_name,
        known_entities=media_retrieval_agent.known_entities,
    )

    # 2 — Adverse Media Retrieval
    retrieved = media_retrieval_agent.retrieve(
        query_name=resolved.resolved_name,
        aliases=resolved.aliases,
        top_k=request.top_k,
        threshold=request.threshold,
        use_live_web=request.use_live_web,
    )

    # 3 — Relevance Scoring
    scored = score_articles(retrieved, threshold=request.threshold)

    # 4 — Risk Analysis
    risk_articles, risk_score, risk_category, risk_breakdown = analyze_risk(scored)

    # 5 — Explainability
    explained_articles, explain_report = explain(
        entity_name=resolved.resolved_name,
        articles=risk_articles,
        risk_score=risk_score,
        risk_category=risk_category,
    )

    # 6 — Decision
    response = make_decision(
        resolved_entity=resolved,
        enriched_articles=explained_articles,
        risk_score=risk_score,
        risk_category=risk_category,
        risk_breakdown=risk_breakdown,
        explainability_report=explain_report,
        start_time=t0,
    )

    return response


# ── Audit Endpoints ───────────────────────────────────────────────────────────

@router.post("/audit", status_code=status.HTTP_201_CREATED, tags=["audit"])
async def submit_audit(request: AuditRequest) -> Dict[str, str]:
    """Record an analyst decision (Approve / Reject / Escalate)."""
    entry: Dict[str, Any] = {
        "screening_id": request.screening_id,
        "entity_name":  request.entity_name,
        "action":       request.action.value,
        "analyst_notes": request.analyst_notes,
        "risk_score":   request.risk_score,
        "risk_category": request.risk_category.value,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }
    append_audit_entry(entry)
    return {"status": "recorded", "screening_id": request.screening_id}


@router.get("/audit-log", tags=["audit"])
async def get_audit_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve the most recent audit log entries."""
    return read_audit_entries(limit=min(limit, 500))
