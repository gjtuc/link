"""
Step 2 — Dreamer LLM 출력 스키마 (Micro-step S2-1)
==================================================

2단계 출력 계약
---------------
  ``DreamHypothesisBroadList`` — Flash only, 15~20 rows (breadth)
  ``DreamHypothesisList``      — Pro output, 1~5 rows (Fact-Checker 입력)

공통 행: ``DreamHypothesis`` (source_fact_id, subject, state_change, mechanism, lag_minutes)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Flash breadth → Pro compress 파이프라인 상수
FLASH_HYPOTHESIS_MIN = 15
FLASH_HYPOTHESIS_MAX = 20
PRO_HYPOTHESIS_MAX = 5


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


class DreamHypothesisBroadList(BaseModel):
    """Flash 1회 — 넓은 브레인스토밍 (15~20개 후보)."""

    hypotheses: list[DreamHypothesis] = Field(
        ...,
        min_length=FLASH_HYPOTHESIS_MIN,
        max_length=FLASH_HYPOTHESIS_MAX,
        description="물리·운영 파급 후보 (중복·약한 가설 포함 가능).",
    )


class DreamHypothesisList(BaseModel):
    """Pro 1회 압축 — 원문 anchor·중복 제거 후 최대 5개."""

    hypotheses: list[DreamHypothesis] = Field(
        ...,
        min_length=1,
        max_length=PRO_HYPOTHESIS_MAX,
        description="Fact-Checker로 넘길 최종 물리 파급 가설.",
    )
