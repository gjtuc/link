"""Step 3 — Tavily search backend (Micro-step CHECK-S1)."""

from __future__ import annotations

import logging

from deconstructor.agents.fact_checker.schemas import SearchSnippet
from deconstructor.agents.fact_checker.search.base import SearchProvider

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S1] {msg}"
    logger.info(line)
    print(line)


class TavilySearchProvider:
    """tavily-python 클라이언트 래퍼."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, *, max_results: int = 5) -> list[SearchSnippet]:
        _log(f"tavily search query={query!r} max={max_results}")
        try:
            from tavily import TavilyClient
        except ImportError as exc:
            raise RuntimeError(
                "tavily-python is not installed. Run: pip install tavily-python"
            ) from exc

        client = TavilyClient(api_key=self._api_key)
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", []) if isinstance(response, dict) else []

        snippets: list[SearchSnippet] = []
        for item in results:
            snippets.append(
                SearchSnippet(
                    title=str(item.get("title", "")),
                    content=str(item.get("content", "")),
                    url=str(item.get("url", "")),
                )
            )
        _log(f"tavily returned {len(snippets)} snippet(s)")
        return snippets
