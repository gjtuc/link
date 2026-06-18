"""
Pydantic 스키마 — LLM 출력을 기계적 사실·인과 구조로만 제한
============================================================

## 설계 원칙

LLM이 자유 서술을 내놓지 못하도록 **필드를 최소화**했다.
감정·평가·전망·내러티브용 슬롯은 **의도적으로 없음**.

## 다른 AI가 수정할 때

  - 필드 추가: deconstruct 프롬프트(prompts.py), report 섹션, Neo4j MERGE 쿼리(weaver/neo4j_store.py),
    viz 툴팁(pyvis_render.py)까지 연쇄 수정 필요
  - `is_atomic`: verify 노드가 True만 completed_facts로 이동시킴 — 의미 변경 시 routing 주의
  - `reasoning`: 기계적 원자성 판단 메모만. 시장 의견 금지 (NarrativeLeakRule 과 연동)

## 타입 관계

  FactList.facts[] → AtomicFact
  Skeptic 검증 통과 → CausalEdge (source/target fact id + probability + latency)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AtomicFact(BaseModel):
    """
    분해의 최소 단위: 주체(subject) + 관측 가능한 상태 변화(state_change) + 시각.

    서술·형용사·감정·예측 필드는 없다. ``reasoning`` 은 verify 루프용
    **기계적** 원자성 판단 메모일 뿐 시장 의견이 아니다.

    Neo4j :Fact 노드로 저장될 때 id, subject, state_change, timestamp, trigger_event 사용.
  """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="파이프라인 전역 고유 ID. Weaver·Skeptic·Neo4j 키.",
    )
    subject: str = Field(
        ...,
        description="단일 명사/엔티티. 최소 명사구 (예: grid power, factory A power supply).",
        min_length=1,
    )
    state_change: str = Field(
        ...,
        description="건조한 관측 전이 (예: 'power -> off', 'interrupted -> occurred').",
        min_length=1,
    )
    timestamp: datetime | None = Field(
        default=None,
        description="텍스트에서 추론 가능한 시각. 없으면 None (TemporalOrderingRule 등에서 처리).",
    )
    is_atomic: bool = Field(
        default=False,
        description=(
            "True = 더 이상 논리적으로 쪼갤 수 없는 null floor. "
            "False = deconstruct 노드가 다시 분해 시도."
        ),
    )
    reasoning: str = Field(
        default="",
        description="원자성 판단 근거 (기계적). 감정·평가 금지.",
    )

    @field_validator("subject", "state_change", "reasoning")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """LLM이 앞뒤 공백을 넣는 경우 정규화."""
        return value.strip()


class FactList(BaseModel):
    """
    deconstruct LLM 한 번 호출의 구조화 출력.

    LangChain ``with_structured_output(FactList)`` 로 파싱됨.
  """

    facts: list[AtomicFact] = Field(
        ...,
        min_length=1,
        description="현재 입력(헤드라인 또는 비원자 crumb)에서 나온 조각 목록.",
    )


class CausalEdge(BaseModel):
    """
    Skeptic이 **검증한** 두 atomic fact 사이의 기계적 인과 링크.

    probability/latency는 scoring.py 에서 규칙 결과·타임스탬프로 산출.
    bullish/bearish 같은 의미 필드는 없음.
    """

    source_fact_id: str = Field(..., description="원인(cause) fact ID.")
    target_fact_id: str = Field(..., description="결과(effect) fact ID.")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="인과 강도 추정 (낙관이 아닌 규칙 기반 점수).",
    )
    latency: int | None = Field(
        default=None,
        ge=0,
        description="원인→결과 지연(ms). 타임스탬프 차이에서 계산.",
    )

    @field_validator("source_fact_id", "target_fact_id")
    @classmethod
    def strip_ids(cls, value: str) -> str:
        return value.strip()
