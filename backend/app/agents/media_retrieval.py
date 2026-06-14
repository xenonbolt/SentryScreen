"""
media_retrieval.py — Adverse Media Retrieval Agent
====================================================
Loads the synthetic dataset, encodes all articles with a
SentenceTransformer model (AMD ROCm / CUDA / CPU), builds a FAISS
inner-product index, and retrieves the top-K most semantically
similar articles for a given entity query.

Live-web mode mimics a human analyst by firing three targeted
Google-style queries per entity:
  1. "Latest {entity} News"            — general recency
  2. "Recent Negative News {entity}"   — adverse signal harvest
  3. "{entity} layoffs OR fraud OR ..."— financial risk keywords
Each matching page is fully read (newspaper3k → BeautifulSoup fallback)
and tagged with is_negative_news based on which query retrieved it.
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

# ── Adverse keyword clusters for the third query ───────────────────────────────
_ADVERSE_KEYWORDS = (
    "layoffs OR \"job cuts\" OR fraud OR lawsuit OR bankruptcy OR scandal "
    "OR fine OR penalty OR corruption OR \"data breach\" OR investigation"
)


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
            use_live_web: If True, perform live web scraping instead of FAISS lookup.

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

            entity_lower = article["entity_name"].lower()
            query_lower  = query_name.lower()
            
            is_match = (
                query_lower in entity_lower or 
                entity_lower in query_lower or
                any(a.lower() in entity_lower for a in aliases)
            )
            
            # If the article is about a completely different entity in the DB, skip it.
            if not is_match:
                continue

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
        """
        Mimics a human analyst Googling an entity in three passes:

          Pass 1 — "Latest {entity} News"
            → General recent news; marks is_negative_news=False by default.

          Pass 2 — "Recent Negative News {entity}"
            → Specifically targets adverse coverage; marks is_negative_news=True.

          Pass 3 — "{entity} layoffs OR fraud OR lawsuit OR ..."
            → Financial / legal risk keywords; marks is_negative_news=True.

        Each result URL is visited and fully read (newspaper3k preferred,
        BeautifulSoup <article>/<main>/<p> fallback) — mimicking a human
        clicking a link and reading the page.
        """
        from duckduckgo_search import DDGS
        from datetime import datetime, timezone

        logger.info(
            f"[MediaRetrieval] Live web — 3-query human-style search for: '{query_name}'"
        )

        raw_articles: List[Dict[str, Any]] = []
        seen_urls: set = set()

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def _normalise_date(raw) -> str:
            if not raw:
                return now_str
            s = str(raw)
            if "T" in s:
                return s[:19] + "Z"
            if len(s) >= 10:
                return s[:10] + "T00:00:00Z"
            return now_str

        # ── 1. Smart full-page reader (newspaper3k → BeautifulSoup) ───────
        def _read_page(url: str, fallback: str) -> str:
            """
            Fully read a webpage the way a human would — prioritise article body.
            Strategy:
              A. newspaper3k  — cleans ads/nav/footers automatically
              B. <article> / <main> tag extraction via BeautifulSoup
              C. All <p> tags joined
              D. DDG snippet fallback
            """
            if not url or url in seen_urls:
                return fallback

            import requests as _req
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            }

            # ── A. newspaper3k ─────────────────────────────────────────
            try:
                from newspaper import Article as _NpArticle
                np_art = _NpArticle(url)
                np_art.download()
                np_art.parse()
                text = (np_art.text or "").strip()
                if len(text) > 200:
                    logger.debug(f"[MediaRetrieval] newspaper3k extracted {len(text)} chars from {url}")
                    return text[:5000]
            except Exception as exc:
                logger.debug(f"[MediaRetrieval] newspaper3k failed ({url}): {exc}")

            # ── B + C. BeautifulSoup fallback ──────────────────────────
            try:
                resp = _req.get(url, headers=headers, timeout=8)
                if resp.status_code != 200:
                    return fallback

                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove noise elements
                for tag in soup(["script", "style", "nav", "header",
                                 "footer", "aside", "form", "noscript"]):
                    tag.decompose()

                # Prefer semantic article/main containers
                container = soup.find("article") or soup.find("main")
                if container:
                    text = " ".join(
                        p.get_text(" ", strip=True)
                        for p in container.find_all("p")
                    )
                    if len(text) > 200:
                        return text[:5000]

                # Fall back to all <p>
                text = " ".join(
                    p.get_text(" ", strip=True)
                    for p in soup.find_all("p")
                )
                if len(text) > len(fallback):
                    return text[:5000]

            except Exception as exc:
                logger.debug(f"[MediaRetrieval] BeautifulSoup scrape failed ({url}): {exc}")

            return fallback

        # ── Query definitions ──────────────────────────────────────────────
        queries: List[Dict[str, Any]] = [
            {
                "label":           "general_news",
                "ddg_query":       f"Latest {query_name} News",
                "search_type":     "news",
                "is_negative":     False,
                "category":        "NEWS",
                "severity_label":  "MEDIUM",
                "max_results":     top_k,
            },
            {
                "label":           "negative_news",
                "ddg_query":       f"Recent Negative News {query_name}",
                "search_type":     "news",
                "is_negative":     True,
                "category":        "NEGATIVE_NEWS",
                "severity_label":  "HIGH",
                "max_results":     top_k,
            },
            {
                "label":           "adverse_keywords",
                "ddg_query":       f"{query_name} {_ADVERSE_KEYWORDS}",
                "search_type":     "text",
                "is_negative":     True,
                "category":        "ADVERSE_MEDIA",
                "severity_label":  "HIGH",
                "max_results":     top_k,
            },
        ]

        try:
            with DDGS() as ddgs:
                for q in queries:
                    logger.info(
                        f"[MediaRetrieval] Query [{q['label']}]: \"{q['ddg_query']}\""
                    )
                    try:
                        if q["search_type"] == "news":
                            hits = list(ddgs.news(q["ddg_query"], max_results=q["max_results"]))
                        else:
                            hits = list(ddgs.text(q["ddg_query"], max_results=q["max_results"]))

                        logger.info(
                            f"[MediaRetrieval]   → {len(hits)} raw hits from DDG [{q['label']}]"
                        )

                        fetched_this_query = 0
                        for r in hits:
                            url   = r.get("url") or r.get("href", "")
                            title = r.get("title", "").strip()
                            body  = r.get("body", "").strip()

                            if not title:
                                continue
                            if url in seen_urls:
                                logger.debug(f"[MediaRetrieval] Skipping duplicate URL: {url}")
                                continue

                            seen_urls.add(url)

                            # ── Read the full page (mimics human clicking the link) ──
                            full_text = _read_page(url, body)
                            if not full_text.strip():
                                full_text = title  # last resort

                            art_id = f"LIVE_{q['label'].upper()}_{len(raw_articles)}"
                            raw_articles.append({
                                "id":               art_id,
                                "entity_name":      query_name,
                                "article_title":    title,
                                "article_text":     full_text[:4000],
                                "source":           url,
                                "published_date":   _normalise_date(r.get("date")),
                                "category":         q["category"],
                                "severity_label":   q["severity_label"],
                                "country":          r.get("source", "Unknown"),
                                "is_negative_news": q["is_negative"],
                                "_query_label":     q["label"],   # internal tag, stripped later
                            })
                            fetched_this_query += 1

                        logger.info(
                            f"[MediaRetrieval]   → {fetched_this_query} new articles collected "
                            f"[{q['label']}]"
                        )

                    except Exception as exc:
                        logger.warning(
                            f"[MediaRetrieval] DDG query [{q['label']}] failed: {exc}"
                        )

        except Exception as exc:
            logger.error(f"[MediaRetrieval] DDGS session error: {exc}")

            logger.info("[MediaRetrieval] Falling back to googlesearch-python...")
            try:
                from googlesearch import search as google_search
                for q in queries:
                    logger.info(f"[MediaRetrieval] Google Query [{q['label']}]: \"{q['ddg_query']}\"")
                    try:
                        hits = list(google_search(q["ddg_query"], num_results=q["max_results"], advanced=True))
                        logger.info(f"[MediaRetrieval]   → {len(hits)} raw hits from Google [{q['label']}]")
                        
                        fetched_this_query = 0
                        for r in hits:
                            if isinstance(r, str):
                                url = r
                                title = r
                                body = ""
                            else:
                                url = getattr(r, 'url', str(r))
                                title = getattr(r, 'title', url)
                                body = getattr(r, 'description', "")
                                
                            if not title or url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            full_text = _read_page(url, body)
                            if not full_text.strip():
                                full_text = title
                                
                            art_id = f"LIVE_GOOG_{q['label'].upper()}_{len(raw_articles)}"
                            raw_articles.append({
                                "id":               art_id,
                                "entity_name":      query_name,
                                "article_title":    title,
                                "article_text":     full_text[:4000],
                                "source":           url,
                                "published_date":   now_str,
                                "category":         q["category"],
                                "severity_label":   q["severity_label"],
                                "country":          "Unknown",
                                "is_negative_news": q["is_negative"],
                                "_query_label":     q["label"],
                            })
                            fetched_this_query += 1
                        logger.info(f"[MediaRetrieval]   → {fetched_this_query} new articles collected (Google)")
                    except Exception as exc_inner:
                         logger.warning(f"[MediaRetrieval] Google query failed: {exc_inner}")
            except ImportError:
                 logger.error("[MediaRetrieval] googlesearch-python not installed. Add it to requirements.txt")
            except Exception as exc_out:
                 logger.error(f"[MediaRetrieval] Google search fallback failed: {exc_out}")

        # ── Wikipedia fallback ─────────────────────────────────────────────
        if not raw_articles:
            logger.warning(
                "[MediaRetrieval] All DDG queries returned 0 hits — trying Wikipedia fallback..."
            )
            try:
                import requests as _req
                wiki_url = (
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/"
                    f"{query_name.replace(' ', '_')}"
                )
                resp = _req.get(wiki_url, headers={"User-Agent": "SentryScreen/1.0"}, timeout=5)
                if resp.status_code == 200:
                    wiki_data = resp.json()
                    title   = wiki_data.get("title", query_name)
                    extract = wiki_data.get("extract", "")
                    if extract:
                        raw_articles.append({
                            "id":               "LIVE_WIKI",
                            "entity_name":      query_name,
                            "article_title":    f"Wikipedia: {title}",
                            "article_text":     extract[:4000],
                            "source":           wiki_data.get("content_urls", {})
                                                         .get("desktop", {})
                                                         .get("page", wiki_url),
                            "published_date":   now_str,
                            "category":         "BACKGROUND_INFO",
                            "severity_label":   "LOW",
                            "country":          "Global",
                            "is_negative_news": False,
                            "_query_label":     "wikipedia_fallback",
                        })
            except Exception as exc:
                logger.warning(f"[MediaRetrieval] Wikipedia fallback failed: {exc}")

        if not raw_articles:
            logger.warning("[MediaRetrieval] No live articles retrieved even with fallback.")
            return []

        logger.info(
            f"[MediaRetrieval] Scoring {len(raw_articles)} live articles "
            f"({sum(1 for a in raw_articles if a.get('is_negative_news'))} tagged negative)..."
        )

        # ── Semantic scoring ───────────────────────────────────────────────
        encode_texts = [
            f"{a['article_title']} {a['article_text'][:400]}"
            for a in raw_articles
        ]
        art_vecs = self.model.encode(
            encode_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

        # Query vector — entity name + aliases for richer signal
        query_parts  = [query_name] + aliases[:3]
        query_text   = " ".join(dict.fromkeys(query_parts))
        q_vec = self.model.encode(
            [query_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)[0]

        # Lower threshold for live results (snippets are shorter → lower cosine)
        live_threshold = min(threshold * 0.5, 0.10)

        results: List[Tuple[Dict[str, Any], float]] = []
        for i, art in enumerate(raw_articles):
            score = float(np.dot(q_vec, art_vecs[i]))
            if score >= live_threshold:
                # Strip internal _query_label before handing off
                clean_art = {k: v for k, v in art.items() if k != "_query_label"}
                results.append((clean_art, round(score, 6)))

        results.sort(key=lambda x: x[1], reverse=True)
        neg_count = sum(1 for a, _ in results if a.get("is_negative_news"))
        logger.info(
            f"[MediaRetrieval] Live results: {len(results)} above threshold={live_threshold:.3f} "
            f"({neg_count} negative-tagged)"
        )
        
        # Persist these live articles so they are available in future sessions
        clean_articles_to_add = [a for a, _ in results]
        self.add_articles(clean_articles_to_add)
        
        return results[:top_k]

    def add_articles(self, new_articles: List[Dict[str, Any]]):
        """Append live articles to the synthetic dataset and update FAISS index."""
        if not new_articles:
            return
            
        import uuid
        import json
        
        # Add to in-memory list
        self.articles.extend(new_articles)
        
        # Update FAISS
        encode_texts = [f"{a['article_title']} {a['article_text'][:400]}" for a in new_articles]
        new_vecs = self.model.encode(
            encode_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)
        self.index.add(new_vecs)
        self.dataset_size = len(self.articles)
        
        # Append to json
        try:
            with open(SYNTHETIC_DATA_FILE, "r") as f:
                data = json.load(f)
            data.extend(new_articles)
            with open(SYNTHETIC_DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"[MediaRetrieval] Appended {len(new_articles)} live articles to dataset. FAISS updated.")
        except Exception as e:
            logger.error(f"[MediaRetrieval] Failed to persist new articles: {e}")

# ── Module-level singleton ────────────────────────────────────────────────────
media_retrieval_agent = MediaRetrievalAgent()
