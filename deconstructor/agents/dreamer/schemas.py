"""
Step 2 — Dreamer LLM 출력 스키마 (Micro-step S2-1)
==================================================
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DreamHypothesis(BaseModel):
    """몽상가가 생성한 단일 파급 효과 가설."""

    source_fact_id: str = Field(
        ...,
        description="이 가설을 유발한 원천 completed_fact ID.",
    )
    subject: str = Field(..., min_length=1, description="파급 효과 주체 (명사구).")
    state_change: str = Field(
        ...,
        min_length=1,
        description="물리적 상태 전이 (예: production -> halted).",
    )
    lag_minutes: int | None = Field(
        default=None,
        ge=0,
        description="원천 fact timestamp 대비 지연(분). 없으면 null.",
    )
    mechanism: str = Field(
        ...,
        min_length=10,
        description="A가 물리적으로 B를 강제하는 기계적 연쇄 설명.",
    )

    @field_validator("source_fact_id", "subject", "state_change", "mechanism")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class DreamHypothesisList(BaseModel):
    """LLM structured output — 3~5개 직접 파급 효과."""

    hypotheses: list[DreamHypothesis] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="물리·거시경제적으로 강제되는 직접 파급 효과.",
    )
