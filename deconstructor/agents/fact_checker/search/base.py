"""Step 3 — Search provider protocol."""

from __future__ import annotations

from typing import Protocol

from deconstructor.agents.fact_checker.schemas import SearchSnippet


class SearchProvider(Protocol):
    """Tavily 등 웹 검색 백엔드."""

    def search(self, query: str, *, max_results: int = 5) -> list[SearchSnippet]:
        ...
