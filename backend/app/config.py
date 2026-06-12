"""
config.py — Central Configuration
====================================
All constants, weights, paths, and device detection for the
Adverse Media Screening Copilot. Optimised for AMD MI300X (ROCm).
"""

import os
import logging
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("adverse_media")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
AUDIT_LOG_DIR = BASE_DIR.parent / "audit_log"
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "decisions.jsonl"

# ── Device Detection (AMD ROCm / CUDA / CPU) ──────────────────────────────────
def _detect_device() -> tuple[str, str]:
    """
    Detect the best available compute device.
    On AMD MI300X, ROCm exposes itself as 'cuda' via the HIP backend.
    Returns (device_str, human_readable_name).
    """
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU detected: {dev_name}  →  using device='cuda' (ROCm/CUDA)")
            return "cuda", dev_name
    except ImportError:
        pass
    logger.info("No GPU detected — falling back to CPU.")
    return "cpu", "CPU"

DEVICE, DEVICE_NAME = _detect_device()

# ── Model ─────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL      = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
TOP_K_RESULTS        = int(os.getenv("TOP_K_RESULTS", "15"))
RELEVANCE_THRESHOLD  = float(os.getenv("RELEVANCE_THRESHOLD", "0.20"))

# ── Risk Scoring Weights ──────────────────────────────────────────────────────
#  Risk = 0.35*relevance + 0.25*severity + 0.25*frequency + 0.15*recency
WEIGHT_RELEVANCE  = 0.35
WEIGHT_SEVERITY   = 0.25
WEIGHT_FREQUENCY  = 0.25
WEIGHT_RECENCY    = 0.15

RECENCY_HALF_LIFE_DAYS = 365   # 50 % decay after 1 year

SEVERITY_WEIGHTS: dict[str, float] = {
    "critical": 1.00,
    "high":     0.75,
    "medium":   0.50,
    "low":      0.25,
}

RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "LOW":    (0.0,  30.0),
    "MEDIUM": (30.1, 70.0),
    "HIGH":   (70.1, 100.0),
}

# ── Entity Resolution ─────────────────────────────────────────────────────────
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", "65"))

# ── Optional On-Prem LLM via Ollama ──────────────────────────────────────────
OLLAMA_ENABLED  = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3")

# ── Dataset ───────────────────────────────────────────────────────────────────
DATASET_FILE = DATA_DIR / "synthetic_dataset.json"

# ── API ───────────────────────────────────────────────────────────────────────
API_VERSION = "1.0.0"
APP_TITLE   = "Adverse Media Screening Copilot"
