"""Step 3 — Search factory + API key validation (Micro-step CHECK-S1)."""

from __future__ import annotations

import logging

from deconstructor import config
from deconstructor.agents.fact_checker.search.base import SearchProvider
from deconstructor.agents.fact_checker.search.tavily import TavilySearchProvider

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S1] {msg}"
    logger.info(line)
    print(line)


def require_tavily_api_key() -> str:
    """
    TAVILY_API_KEY 검증. 없으면 친절한 RuntimeError.

    Micro-step CHECK-S1-validate
    """
    key = config.TAVILY_API_KEY
    if not key:
        _log("MISSING TAVILY_API_KEY")
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Fact-Checker live search requires Tavily.\n"
            "  1. Get a key at https://tavily.com\n"
            "  2. Set TAVILY_API_KEY in .env or deconstructor/local_settings.py\n"
            "  3. Or use --dry-run / stub mode (no Tavily needed)"
        )
    _log("TAVILY_API_KEY present")
    return key


def get_search_provider() -> SearchProvider:
    """Live Fact-Checker용 Tavily provider."""
    key = require_tavily_api_key()
    return TavilySearchProvider(api_key=key)
