"""
main.py — FastAPI Application Entry Point
==========================================
Configures the FastAPI app, registers routers, initialises the
MediaRetrieval agent (model + FAISS index) on startup, and wires up
request-level logging middleware.

CORS is disabled (allow all origins) for on-premises deployment.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.agents.media_retrieval import media_retrieval_agent
from app.api.routes import router
from app.config import API_VERSION, APP_TITLE, DEVICE, DEVICE_NAME, LOG_FILE
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
    logger.info("=" * 60)
    logger.info(f"  {APP_TITLE}  v{API_VERSION}")
    logger.info(f"  Compute device : {DEVICE} ({DEVICE_NAME})")
    logger.info(f"  Log file       : {LOG_FILE}")
    logger.info("=" * 60)

    # Auto-generate dataset if not present
    from app.config import DATASET_FILE
    if not DATASET_FILE.exists():
        logger.info("Dataset not found — generating...")
        generate_dataset()

    # Load SentenceTransformer and build FAISS index
    logger.info("Initialising MediaRetrieval agent...")
    media_retrieval_agent.initialize()
    logger.info("Agent ready — API is accepting requests.")

    yield   # ← application is running

    logger.info(f"=== {APP_TITLE} shutting down ===")


# ── Request Logging Middleware ─────────────────────────────────────────────────

async def _request_logging_middleware(request: Request, call_next) -> Response:
    """
    Log every HTTP request with:
      - Unique request ID (X-Request-ID header)
      - Method + path + query string
      - Response status code
      - Wall-clock duration in ms
    WARNING/ERROR log levels are used for 4xx/5xx responses.
    """
    req_id = str(uuid.uuid4())[:8]
    method = request.method
    path   = request.url.path
    qs     = f"?{request.url.query}" if request.url.query else ""

    is_telemetry = path.endswith("/telemetry")
    if not is_telemetry:
        logger.info(f"[{req_id}] ▶ {method} {path}{qs}")

    t0 = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error(
            f"[{req_id}] ✗ {method} {path} — UNHANDLED EXCEPTION "
            f"({elapsed:.1f}ms): {exc}",
            exc_info=True,
        )
        raise

    elapsed_ms = (time.perf_counter() - t0) * 1000
    status     = response.status_code

    log_fn = logger.info
    marker = "✓"
    if 400 <= status < 500:
        log_fn = logger.warning
        marker = "⚠"
    elif status >= 500:
        log_fn = logger.error
        marker = "✗"

    if not (is_telemetry and status == 200):
        log_fn(
            f"[{req_id}] {marker} {method} {path} → {status} ({elapsed_ms:.1f}ms)"
        )

    # Propagate the request ID so clients can correlate logs
    response.headers["X-Request-ID"] = req_id
    return response

async def _jupyter_proxy_middleware(request: Request, call_next) -> Response:
    """
    Jupyter Server Proxy sends requests with the proxy path in X-Forwarded-Context.
    By dynamically setting request.scope['root_path'], FastAPI automatically
    fixes the Swagger UI /openapi.json links without hardcoding the workspace ID!
    """
    if "x-forwarded-context" in request.headers:
        request.scope["root_path"] = request.headers["x-forwarded-context"]
    return await call_next(request)


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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request logging & Jupyter Proxy handling ──────────────────────────
    app.middleware("http")(_request_logging_middleware)
    app.middleware("http")(_jupyter_proxy_middleware)

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(router, prefix="/api")

    return app


app = create_app()
