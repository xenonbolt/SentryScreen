"""
schemas.py — Pydantic v2 Data Models
======================================
All request/response models used across agents and API routes.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────

class RiskCategory(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


class SeverityLabel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class EntityType(str, Enum):
    COMPANY = "company"
    PERSON  = "person"
    UNKNOWN = "unknown"


class AuditAction(str, Enum):
    APPROVE  = "APPROVE"
    REJECT   = "REJECT"
    ESCALATE = "ESCALATE"


# ── Requests ──────────────────────────────────────────────────────────────────

class ScreeningRequest(BaseModel):
    entity_name: str = Field(
        ..., min_length=2, max_length=300,
        description="Name of the company or person to screen.",
        examples=["Nexum Capital Partners", "Viktor Dragan"],
    )
    top_k: int = Field(default=10, ge=1, le=50, description="Max articles to return.")
    threshold: float = Field(
        default=0.20, ge=0.0, le=1.0,
        description="Minimum cosine similarity threshold.",
    )
    use_live_web: bool = Field(default=False, description="If True, performs live web scraping via DuckDuckGo")
    search_engine: str = Field(default="duckduckgo", description="The search engine to use ('duckduckgo' or 'google')")


class AuditRequest(BaseModel):
    screening_id: str
    entity_name:  str
    source:       Optional[str] = None
    action:       AuditAction
    analyst_notes: Optional[str] = None
    risk_score:   float
    risk_category: RiskCategory


# ── Agent Output Models ───────────────────────────────────────────────────────

class ResolvedEntity(BaseModel):
    original_name:  str
    resolved_name:  str
    confidence:     float = Field(ge=0.0, le=1.0)
    aliases:        List[str]
    entity_type:    EntityType


class ArticleResult(BaseModel):
    id:             str
    entity_name:    str
    article_title:  str
    article_text:   str
    source:         str
    published_date: str
    category:       str
    severity_label: SeverityLabel
    country:        str
    relevance_score:  float
    risk_contribution: float
    keywords:       List[str]
    evidence_quotes: List[str] = Field(default_factory=list)
    why_flagged:    str
    relevance_reason: str
    sentiment_score: float = Field(default=0.0, ge=0.0, le=1.0,
                                   description="Negative sentiment intensity (0=neutral, 1=max negative)")
    is_negative_news: bool = Field(default=False,
                                   description="True when article was retrieved via adverse/negative query or classified as negative by ZSC")


class RiskBreakdown(BaseModel):
    relevance_component:  float   # 0–30
    severity_component:   float   # 0–22
    frequency_component:  float   # 0–20
    recency_component:    float   # 0–13
    sentiment_component:  float = 0.0   # 0–15 (NEW)
    negative_news_count:  int   = 0     # number of articles flagged as negative news


class ExplainabilityReport(BaseModel):
    summary:               str
    key_risk_factors:      List[str]
    category_distribution: Dict[str, int]
    top_keywords:          List[str]
    timeline_analysis:     str
    confidence_explanation: str


# ── Final Response ────────────────────────────────────────────────────────────

class ScreeningResponse(BaseModel):
    screening_id:      str
    entity:            ResolvedEntity
    articles:          List[ArticleResult]
    risk_score:        float = Field(ge=0.0, le=100.0)
    risk_category:     RiskCategory
    confidence_score:  float = Field(ge=0.0, le=1.0)
    risk_breakdown:    RiskBreakdown
    explainability:    ExplainabilityReport
    total_articles_found: int
    device_used:       str
    processing_time_ms: float
    timestamp:         datetime


# ── Audit / Health ────────────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    screening_id:  str
    entity_name:   str
    action:        AuditAction
    analyst_notes: Optional[str] = None
    risk_score:    float
    risk_category: RiskCategory
    timestamp:     datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status:        str
    device:        str
    device_name:   str
    model_loaded:  bool
    dataset_size:  int
    version:       str
    vram_usage:    Optional[int] = None
    compute_load:  Optional[int] = None
    cpu_usage:     Optional[int] = None
    ram_usage:     Optional[int] = None


class DatasetStats(BaseModel):
    total_articles:       int
    unique_entities:      int
    category_counts:      Dict[str, int]
    severity_counts:      Dict[str, int]
    date_range:           Dict[str, str]
    countries:            List[str]
