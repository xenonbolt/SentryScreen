"""
entity_resolver.py — Entity Resolver Agent
============================================
Disambiguates user-supplied entity names against the dataset using
fuzzy token matching (RapidFuzz), legal suffix normalisation, and
alias expansion. Designed to handle variations like:
  "ABC Ltd"  →  "ABC Limited"  →  "ABC Holdings"
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

from rapidfuzz import fuzz, process

from app.config import FUZZY_MATCH_THRESHOLD
from app.models.schemas import EntityType, ResolvedEntity

logger = logging.getLogger(__name__)


# ── Legal suffix patterns stripped during normalisation ───────────────────────
_LEGAL_SUFFIXES = [
    r"\bltd\.?\b", r"\bllc\.?\b", r"\bllp\.?\b", r"\binc\.?\b",
    r"\bcorp\.?\b", r"\bcorporation\b", r"\blimited\b", r"\bholding(s)?\b",
    r"\bgroup\b", r"\bplc\.?\b", r"\bs\.a\.?\b", r"\bgmbh\b",
    r"\bag\b", r"\bco\.?\b", r"\bcompany\b", r"\bpartner(s)?\b",
    r"\bassociate(s)?\b", r"\bventure(s)?\b", r"\bcapital\b",
    r"\binternational\b", r"\bglobal\b",
]

# Word-level synonyms used for alias expansion
_SYNONYMS: Dict[str, List[str]] = {
    "limited": ["ltd", "llc", "llp", "inc", "corp"],
    "corporation": ["corp", "inc", "co"],
    "international": ["intl", "int'l", "intl."],
    "technologies": ["tech", "technology", "systems"],
    "financial": ["fin", "finance", "financial services"],
    "holdings": ["holding", "group", "capital"],
    "services": ["svc", "svcs", "service"],
}

# Company indicators for heuristic type detection
_COMPANY_TOKENS = {
    "ltd", "llc", "inc", "corp", "group", "holdings", "bank", "fund",
    "capital", "investment", "technologies", "solutions", "services",
    "international", "global", "partners", "associates", "ventures",
    "resources", "energy", "mining", "pharma", "shipping", "financial",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalise(name: str) -> str:
    """Lowercase, strip legal suffixes, collapse whitespace."""
    s = name.lower().strip()
    for pattern in _LEGAL_SUFFIXES:
        s = re.sub(pattern, "", s, flags=re.IGNORECASE)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _detect_type(name: str) -> EntityType:
    """Heuristic: does the name look like a company or a person?"""
    tokens = name.lower().split()
    if any(tok in _COMPANY_TOKENS for tok in tokens):
        return EntityType.COMPANY
    # Person-like: 2–4 capitalised words, no company token
    words = name.strip().split()
    if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
        return EntityType.PERSON
    return EntityType.UNKNOWN


def _expand_aliases(name: str) -> List[str]:
    """Generate common spelling variants of the entity name."""
    aliases: List[str] = [name]
    lower = name.lower()
    for canonical, variants in _SYNONYMS.items():
        if canonical in lower:
            for v in variants:
                aliases.append(re.sub(canonical, v, lower))
        for v in variants:
            if v in lower:
                aliases.append(re.sub(re.escape(v), canonical, lower))
    aliases.append(_normalise(name))
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: List[str] = []
    for a in aliases:
        if a not in seen and a.strip():
            seen.add(a)
            result.append(a)
    return result


# ── Main Agent Function ───────────────────────────────────────────────────────

def resolve_entity(
    query_name: str,
    known_entities: List[str],
) -> ResolvedEntity:
    """
    Resolve a user-supplied entity name against the corpus of known entity names.

    Strategy:
    1. Normalise query and all known entities.
    2. Expand query into aliases.
    3. Use RapidFuzz token_sort_ratio to find the best matching known entity.
    4. Return resolved entity with confidence and aliases.

    Args:
        query_name:     Name provided by the analyst.
        known_entities: All unique entity names in the dataset.

    Returns:
        ResolvedEntity dataclass.
    """
    logger.info(f"[EntityResolver] Resolving: '{query_name}'")

    entity_type = _detect_type(query_name)
    query_aliases = _expand_aliases(query_name)

    # Build mapping: normalised → original
    norm_to_orig: Dict[str, str] = {_normalise(e): e for e in known_entities}
    candidates = list(norm_to_orig.keys())

    best_match_norm = ""
    best_score = 0.0

    for alias in query_aliases:
        alias_norm = _normalise(alias)
        if not alias_norm:
            continue
        hits: List[Tuple[str, float, int]] = process.extract(
            alias_norm, candidates, scorer=fuzz.token_sort_ratio, limit=5
        )
        for match_norm, score, _ in hits:
            if score > best_score:
                best_score = score
                best_match_norm = match_norm

    confidence = round(best_score / 100.0, 3)

    if best_score < FUZZY_MATCH_THRESHOLD or not best_match_norm:
        # No strong match — proceed with original query (broad search)
        resolved_name = query_name
        confidence = max(confidence, 0.40)   # floor so pipeline still runs
        logger.warning(
            f"[EntityResolver] No confident match for '{query_name}' "
            f"(best score={best_score:.1f}). Proceeding with original name."
        )
    else:
        resolved_name = norm_to_orig[best_match_norm]
        logger.info(
            f"[EntityResolver] '{query_name}' → '{resolved_name}' "
            f"(score={best_score:.1f}, confidence={confidence:.3f})"
        )

    display_aliases = [
        a for a in _expand_aliases(resolved_name)
        if a.strip().lower() != resolved_name.lower()
    ][:6]

    return ResolvedEntity(
        original_name=query_name,
        resolved_name=resolved_name,
        confidence=confidence,
        aliases=display_aliases,
        entity_type=entity_type,
    )
