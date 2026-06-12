"""
media_retrieval.py — Adverse Media Retrieval Agent
====================================================
Loads the synthetic dataset, encodes all articles with a
SentenceTransformer model (AMD ROCm / CUDA / CPU), builds a FAISS
inner-product index, and retrieves the top-K most semantically
similar articles for a given entity query.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import (
    DATASET_FILE, DEVICE, EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL, RELEVANCE_THRESHOLD, TOP_K_RESULTS,
)

logger = logging.getLogger(__name__)


class MediaRetrievalAgent:
    """
    Singleton agent that manages the FAISS vector index.
    Call `initialize()` once at application startup.
    """

    def __init__(self) -> None:
        self.model = None
        self.index = None
        self.articles: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self._gpu_index: bool = False
        self._initialized: bool = False

    # ── Initialisation ─────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Load model, dataset, and build FAISS index. Idempotent."""
        if self._initialized:
            return

        # 1. Load the SentenceTransformer model
        logger.info(f"[MediaRetrieval] Loading '{EMBEDDING_MODEL}' on device='{DEVICE}'")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

        # 2. Load dataset
        self.articles = self._load_dataset()

        # 3. Encode and index
        self._build_faiss_index()

        self._initialized = True
        logger.info("[MediaRetrieval] Initialised — ready for queries.")

    def _load_dataset(self) -> List[Dict[str, Any]]:
        if not DATASET_FILE.exists():
            # Auto-generate if missing
            logger.warning("[MediaRetrieval] Dataset not found — auto-generating...")
            from app.data.generate_dataset import main as gen_main
            gen_main()

        with open(DATASET_FILE, encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)

        logger.info(f"[MediaRetrieval] Loaded {len(data)} articles.")
        return data

    def _build_faiss_index(self) -> None:
        """Encode articles and build FAISS flat inner-product index."""
        import faiss  # imported here to allow graceful fallback

        texts = [
            f"{a['entity_name']} {a['article_title']} {a['article_text'][:400]}"
            for a in self.articles
        ]

        t0 = time.perf_counter()
        self.embeddings = self.model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,   # L2-normalise → IP == cosine
        ).astype(np.float32)
        elapsed = time.perf_counter() - t0
        logger.info(
            f"[MediaRetrieval] Encoded {len(texts)} articles in {elapsed:.2f}s "
            f"on {DEVICE} | dim={self.embeddings.shape[1]}"
        )

        dim = self.embeddings.shape[1]
        cpu_index = faiss.IndexFlatIP(dim)
        cpu_index.add(self.embeddings)

        # Try to move index to GPU (faiss-gpu / ROCm build)
        try:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            self._gpu_index = True
            logger.info("[MediaRetrieval] FAISS index moved to GPU.")
        except Exception:
            self.index = cpu_index
            logger.info("[MediaRetrieval] Using CPU FAISS index (faiss-gpu not available).")

    # ── Query ──────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query_name: str,
        aliases: List[str],
        top_k: int = TOP_K_RESULTS,
        threshold: float = RELEVANCE_THRESHOLD,
        use_live_web: bool = False,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find the top-K articles most semantically similar to the entity query.

        Args:
            query_name: Primary entity name (resolved).
            aliases:    Alternative names for the entity.
            top_k:      Maximum number of results to return.
            threshold:  Minimum cosine similarity score.

        Returns:
            Sorted list of (article_dict, similarity_score).
        """
        if not self._initialized:
            self.initialize()

        if use_live_web:
            return self._retrieve_live_web(query_name, aliases, top_k, threshold)

        # Compose a rich query string from the entity name and its aliases
        query_parts = [query_name] + aliases[:4]
        query_text = " | ".join(dict.fromkeys(query_parts))  # dedupe, keep order

        q_vec = self.model.encode(
            [query_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        k_search = min(top_k * 4, len(self.articles))
        scores, indices = self.index.search(q_vec, k_search)

        results: List[Tuple[Dict[str, Any], float]] = []
        seen_ids: set[str] = set()

        for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
            if idx < 0 or score < threshold:
                continue
            article = self.articles[idx]
            art_id = article.get("id", str(idx))
            if art_id in seen_ids:
                continue
            seen_ids.add(art_id)

            # Small boost when entity name appears literally in article
            entity_lower = article["entity_name"].lower()
            query_lower  = query_name.lower()
            if (query_lower in entity_lower or entity_lower in query_lower or
                    any(a.lower() in entity_lower for a in aliases)):
                score = min(1.0, score * 1.15)

            results.append((article, round(float(score), 6)))

        results.sort(key=lambda x: x[1], reverse=True)
        logger.info(
            f"[MediaRetrieval] '{query_name}' → {len(results)} results "
            f"(threshold={threshold}, top_k={top_k})"
        )
        return results[:top_k]

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def dataset_size(self) -> int:
        return len(self.articles)

    @property
    def known_entities(self) -> List[str]:
        return list({a["entity_name"] for a in self.articles})

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Live Web Scraping ──────────────────────────────────────────────────

    def _retrieve_live_web(
        self, query_name: str, aliases: List[str], top_k: int, threshold: float
    ) -> List[Tuple[Dict[str, Any], float]]:
        from duckduckgo_search import DDGS
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime

        search_query = f'"{query_name}" AND (fraud OR money laundering OR sanctions OR indictment OR fine OR arrest OR corruption)'
        logger.info(f"[MediaRetrieval] Live scraping DDG for: {search_query}")

        scraped_articles = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=top_k * 2))
                for r in results:
                    if len(scraped_articles) >= top_k:
                        break
                    url = r.get("href", "")
                    title = r.get("title", "")
                    article_text = ""
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        resp = requests.get(url, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "html.parser")
                            article_text = " ".join([p.get_text() for p in soup.find_all("p")])
                    except Exception as e:
                        logger.warning(f"[MediaRetrieval] Failed to fetch {url}: {e}")
                    
                    if not article_text.strip():
                        article_text = r.get("body", "")
                    if not article_text.strip():
                        continue

                    art = {
                        "id": f"LIVE_{len(scraped_articles)}",
                        "entity_name": query_name,
                        "article_title": title,
                        "article_text": article_text[:3000],
                        "source": url,
                        "published_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "category": "LIVE_WEB_HIT",
                        "severity_label": "HIGH",
                        "country": "Unknown"
                    }
                    scraped_articles.append(art)
        except Exception as e:
            logger.error(f"[MediaRetrieval] DDGS Error: {e}")

        if not scraped_articles:
            return []

        # Encode and score dynamically
        texts = [f"{a['entity_name']} {a['article_title']} {a['article_text'][:400]}" for a in scraped_articles]
        art_embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        
        q_vec = self.model.encode([query_name], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)[0]
        
        results = []
        for i, art in enumerate(scraped_articles):
            score = float(np.dot(q_vec, art_embeddings[i]))
            if score >= threshold:
                results.append((art, round(score, 6)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results


# ── Module-level singleton ────────────────────────────────────────────────────
media_retrieval_agent = MediaRetrievalAgent()
