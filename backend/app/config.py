"""
config.py — Central Configuration
====================================
All constants, weights, paths, and device detection for the
Adverse Media Screening Copilot. Optimised for AMD MI300X (ROCm).
"""

import os
import logging
import logging.handlers
import sys
from pathlib import Path

# ── Logging ─────────────────────────────────────────────────────────────────────

# ── Paths (defined early so LOG_DIR can use BASE_DIR) ──────────────────────
BASE_DIR_EARLY = Path(__file__).parent.parent  # backend/
LOG_DIR        = BASE_DIR_EARLY / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "sentryscreen.log"


class _ColourFormatter(logging.Formatter):
    """ANSI-coloured log levels for the console handler."""
    _GREY   = "\033[90m"
    _GREEN  = "\033[32m"
    _YELLOW = "\033[33m"
    _RED    = "\033[31m"
    _BOLD_RED = "\033[1;31m"
    _RESET  = "\033[0m"
    _CYAN   = "\033[36m"

    LEVEL_COLORS = {
        logging.DEBUG:    _GREY,
        logging.INFO:     _GREEN,
        logging.WARNING:  _YELLOW,
        logging.ERROR:    _RED,
        logging.CRITICAL: _BOLD_RED,
    }

    FMT = "%(asctime)s {lvl}%(levelname)-8s{rst} {cyan}%(name)s{rst} — %(message)s"
    DATEFMT = "%Y-%m-%dT%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        color = self.LEVEL_COLORS.get(record.levelno, self._GREY)
        fmt = self.FMT.format(lvl=color, rst=self._RESET, cyan=self._CYAN)
        formatter = logging.Formatter(fmt, datefmt=self.DATEFMT)
        return formatter.format(record)


def _setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. during reload)

    root.setLevel(logging.DEBUG)

    # ── Console: colour, INFO+ ───────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(_ColourFormatter())
    root.addHandler(console)

    # ── Rotating file: plain text, DEBUG+, 5 MB × 5 backups ───────────────
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "sentence_transformers",
                  "transformers", "faiss"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


_setup_logging()
logger = logging.getLogger("sentryscreen")
logger.info(f"Logging initialised — file: {LOG_FILE}")


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
