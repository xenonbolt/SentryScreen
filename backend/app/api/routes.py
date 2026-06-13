"""
routes.py — FastAPI API Routes
================================
All HTTP endpoints for the Adverse Media Screening Copilot.
"""

from __future__ import annotations

import time
import logging
import random
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

# Global mock state for smooth telemetry
mock_telemetry = {
    "vram_usage": 14200,
    "compute_load": 45,
    "cpu_usage": 25,
    "ram_usage": 128,
}

@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """System health and readiness probe."""
    global mock_telemetry
    mock_telemetry["vram_usage"] = min(24000, max(1000, mock_telemetry["vram_usage"] + random.randint(-500, 1500)))
    mock_telemetry["compute_load"] = min(100, max(5, mock_telemetry["compute_load"] + random.randint(-15, 25)))
    mock_telemetry["cpu_usage"] = min(100, max(2, mock_telemetry["cpu_usage"] + random.randint(-10, 10)))
    mock_telemetry["ram_usage"] = min(256, max(32, mock_telemetry["ram_usage"] + random.randint(-4, 4)))

    return HealthResponse(
        status="ok",
        device=DEVICE,
        device_name=DEVICE_NAME,
        model_loaded=media_retrieval_agent.is_initialized,
        dataset_size=media_retrieval_agent.dataset_size,
        version=API_VERSION,
        vram_usage=mock_telemetry["vram_usage"],
        compute_load=mock_telemetry["compute_load"],
        cpu_usage=mock_telemetry["cpu_usage"],
        ram_usage=mock_telemetry["ram_usage"],
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
    2. Media Retrieval      — FAISS semantic search / live web
    3. Relevance Scorer     — normalise + recency decay
    4. Risk Analyst         — weighted risk formula
    5. Explainability Agent — keywords, narratives, summary
    6. Decision Agent       — final verdict + audit trail
    """
    t0 = time.perf_counter()
    mode = "LIVE-WEB" if request.use_live_web else "DATASET"
    logger.info(
        f"[Pipeline] ── START ── entity='{request.entity_name}' "
        f"mode={mode} top_k={request.top_k} threshold={request.threshold}"
    )

    if not media_retrieval_agent.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval agent is still initialising. Please retry in a few seconds.",
        )

    # ── Step 1: Entity Resolution ─────────────────────────────────────────
    s1 = time.perf_counter()
    resolved = resolve_entity(
        query_name=request.entity_name,
        known_entities=media_retrieval_agent.known_entities,
    )
    t1 = (time.perf_counter() - s1) * 1000
    logger.info(
        f"[Pipeline] Step 1 EntityResolver  {t1:6.1f}ms  "
        f"'{request.entity_name}' → '{resolved.resolved_name}' "
        f"(conf={resolved.confidence:.2f})"
    )

    # ── Step 2: Adverse Media Retrieval ──────────────────────────────────
    s2 = time.perf_counter()
    retrieved = media_retrieval_agent.retrieve(
        query_name=resolved.resolved_name,
        aliases=resolved.aliases,
        top_k=request.top_k,
        threshold=request.threshold,
        use_live_web=request.use_live_web,
    )
    t2 = (time.perf_counter() - s2) * 1000
    logger.info(
        f"[Pipeline] Step 2 MediaRetrieval  {t2:6.1f}ms  "
        f"{len(retrieved)} article(s) retrieved"
    )

    # ── Step 3: Relevance Scoring ─────────────────────────────────────────
    s3 = time.perf_counter()
    scored = score_articles(retrieved, threshold=request.threshold)
    t3 = (time.perf_counter() - s3) * 1000
    logger.info(
        f"[Pipeline] Step 3 RelevanceScorer {t3:6.1f}ms  "
        f"{len(scored)} article(s) above threshold"
    )

    # ── Step 4: Risk Analysis ─────────────────────────────────────────────
    s4 = time.perf_counter()
    risk_articles, risk_score, risk_category, risk_breakdown = analyze_risk(scored)
    t4 = (time.perf_counter() - s4) * 1000
    logger.info(
        f"[Pipeline] Step 4 RiskAnalyst     {t4:6.1f}ms  "
        f"score={risk_score:.1f} category={risk_category.value}"
    )

    # ── Step 5: Explainability ────────────────────────────────────────────
    s5 = time.perf_counter()
    explained_articles, explain_report = explain(
        entity_name=resolved.resolved_name,
        articles=risk_articles,
        risk_score=risk_score,
        risk_category=risk_category,
    )
    t5 = (time.perf_counter() - s5) * 1000
    logger.info(
        f"[Pipeline] Step 5 Explainability  {t5:6.1f}ms  "
        f"{len(explain_report.key_risk_factors)} risk factors, "
        f"{len(explain_report.top_keywords)} keywords"
    )

    # ── Step 6: Decision ──────────────────────────────────────────────────
    s6 = time.perf_counter()
    response = make_decision(
        resolved_entity=resolved,
        enriched_articles=explained_articles,
        risk_score=risk_score,
        risk_category=risk_category,
        risk_breakdown=risk_breakdown,
        explainability_report=explain_report,
        start_time=t0,
    )
    t6 = (time.perf_counter() - s6) * 1000
    total_ms = (time.perf_counter() - t0) * 1000

    logger.info(
        f"[Pipeline] Step 6 Decision        {t6:6.1f}ms  "
        f"screening_id={response.screening_id}"
    )
    logger.info(
        f"[Pipeline] ── DONE ──  total={total_ms:.1f}ms  "
        f"steps=[{t1:.0f}|{t2:.0f}|{t3:.0f}|{t4:.0f}|{t5:.0f}|{t6:.0f}]ms  "
        f"entity='{resolved.resolved_name}'  "
        f"risk={risk_score:.1f}({risk_category.value})  "
        f"articles={len(explained_articles)}"
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


# ── Articles (Compliance Database) ────────────────────────────────────────────

@router.get("/articles", tags=["system"])
async def list_articles(
    limit: int = 30,
    offset: int = 0,
    entity: str = "",
    severity: str = "",
) -> List[Dict[str, Any]]:
    """Return paginated articles from the pre-compiled dataset (Compliance Database)."""
    if not media_retrieval_agent.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not yet initialised.",
        )
    arts = media_retrieval_agent.articles
    if entity:
        arts = [a for a in arts if entity.lower() in a.get("entity_name", "").lower()]
    if severity:
        arts = [a for a in arts if a.get("severity_label", "").lower() == severity.lower()]
    return arts[offset: offset + limit]
