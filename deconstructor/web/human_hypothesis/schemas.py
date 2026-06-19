"""
Human hypothesis — API 스키마 (MVP)
===================================

웹 UI 모달 → ``POST /api/human-hypothesis`` JSON 본문.

필드는 Dreamer ``DreamHypothesis`` 와 1:1 대응하도록 유지한다.
(추후 v3에서 ``note`` 한 줄만 받아 LLM이 3필드로 분해 가능)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class HumanHypothesisCreate(BaseModel):
    """
  파란(extracted) 노드에서 이어지는 사용자 가설 입력.

  anchor_fact_id
      클릭한 원천 Fact의 Neo4j ``id``. 반드시 DB에 존재하고
      ``source_type=extracted``, ``check_status=active`` 여야 한다.
  subject / state_change / mechanism
      Dreamer 출력과 동일 의미. mechanism → AtomicFact.reasoning.
    """

    anchor_fact_id: str = Field(
        ...,
        min_length=1,
        description="원천(extracted) Fact id — 그래프에서 우클릭한 파란 노드.",
    )
    subject: str = Field(
        ...,
        min_length=1,
        description="단일 명사/엔티티 (예: BZY10 grain boundary resistance).",
    )
    state_change: str = Field(
        ...,
        min_length=1,
        description="관측 전이 (예: increased, decreased).",
    )
    mechanism: str = Field(
        default="",
        description="사용자가 적은 메커니즘·근거. AtomicFact.reasoning 으로 저장.",
    )

    @field_validator("anchor_fact_id", "subject", "state_change", "mechanism")
    @classmethod
    def strip_fields(cls, value: str) -> str:
        return value.strip()

    @field_validator("mechanism")
    @classmethod
    def mechanism_optional(cls, value: str) -> str:
        return value or ""


class HumanHypothesisResult(BaseModel):
    """MVP 성공 응답 — 생성된 fact 메타 + 그래프 갱신 여부."""

    ok: bool = True
    fact_id: str
    anchor_fact_id: str
    subject: str
    state_change: str
    author: str = "human"
    source_type: str = "inferred"
    check_status: str = "pending"
    graph_refreshed: bool = False
    steps: list[dict] = Field(default_factory=list)
    message: str = ""
