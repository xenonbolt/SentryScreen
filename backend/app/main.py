"""
main.py — FastAPI Application Entry Point
==========================================
Configures the FastAPI app, registers routers, and initialises the
MediaRetrieval agent (model + FAISS index) on startup.

CORS is disabled (allow all origins) for on-premises deployment.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.media_retrieval import media_retrieval_agent
from app.api.routes import router
from app.config import API_VERSION, APP_TITLE, DEVICE, DEVICE_NAME
from app.data.generate_dataset import main as generate_dataset

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler:
    - Generates dataset if missing.
    - Initialises the MediaRetrieval agent (loads model + FAISS index).
    """
    logger.info(f"=== {APP_TITLE} v{API_VERSION} starting ===")
    logger.info(f"    Compute device : {DEVICE} ({DEVICE_NAME})")

    # Auto-generate dataset if not present
    from app.config import DATASET_FILE
    if not DATASET_FILE.exists():
        logger.info("Dataset not found — generating...")
        generate_dataset()

    # Load SentenceTransformer and build FAISS index
    logger.info("Initialising MediaRetrieval agent...")
    media_retrieval_agent.initialize()
    logger.info("Agent ready. API accepting requests.")

    yield   # ← application is running

    logger.info(f"=== {APP_TITLE} shutting down ===")


# ── App Factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        version=API_VERSION,
        description=(
            "Production-grade Adverse Media / Negative News Screening Copilot. "
            "Six-agent pipeline: entity resolution → retrieval → relevance scoring → "
            "risk analysis → explainability → decision."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS — fully open for on-prem deployment ───────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],         # disable CORS restriction
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(router, prefix="/api")

    return app


app = create_app()
