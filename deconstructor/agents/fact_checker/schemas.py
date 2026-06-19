"""Step 3 — Fact-Checker schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from deconstructor.models import AtomicFact


class SearchSnippet(BaseModel):
    """Tavily 검색 결과 1건."""

    title: str = ""
    content: str = ""
    url: str = ""


class VerificationVerdict(BaseModel):
    """Verifier LLM structured output."""

    accepted: bool = Field(
        ...,
        description="True only if snippets clearly report the hypothesis as fact.",
    )
    reason: str = Field(..., min_length=3, description="Promote or drop rationale.")


class DroppedHypothesis(BaseModel):
    """탈락 가설 + 폐기 사유 (고스트 노드용)."""

    fact_id: str
    subject: str
    state_change: str
    drop_reason: str
    ghost_fact: AtomicFact
