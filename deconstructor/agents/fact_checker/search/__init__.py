"""Step 3 — Search package."""

from deconstructor.agents.fact_checker.search.factory import get_search_provider, require_tavily_api_key

__all__ = ["get_search_provider", "require_tavily_api_key"]
