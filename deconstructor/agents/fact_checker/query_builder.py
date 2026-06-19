"""Step 3 — 검색 쿼리 생성 (Micro-step CHECK-S2)."""

from __future__ import annotations

import logging
import re
from datetime import datetime

from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S2] {msg}"
    logger.info(line)
    print(line)


def _tokenize(text: str) -> list[str]:
    raw = text.replace("->", " ").replace("_", " ")
    tokens = re.findall(r"[a-zA-Z0-9가-힣]{2,}", raw.lower())
    stop = {"the", "and", "percent", "->"}
    return [t for t in tokens if t not in stop][:8]


def build_search_query(fact: AtomicFact) -> str:
    """
    subject + state_change + timestamp → Tavily 쿼리.

    Micro-step CHECK-S2-1..3
    """
    _log(f"build query for subject={fact.subject!r}")
    subject_tokens = _tokenize(fact.subject)
    change_tokens = _tokenize(fact.state_change)
    merged = subject_tokens + [t for t in change_tokens if t not in subject_tokens]

    date_part = ""
    if fact.timestamp:
        if isinstance(fact.timestamp, datetime):
            date_part = fact.timestamp.strftime("%Y-%m-%d")
        else:
            date_part = str(fact.timestamp)[:10]

    query_parts = merged[:6]
    if date_part:
        query_parts.append(date_part)

    query = " ".join(query_parts)
    _log(f"query={query!r}")
    return query
