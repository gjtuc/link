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

from deconstructor.provenance.types import (
    DEFAULT_CHECK_STATUS,
    DEFAULT_SOURCE_TYPE,
    CheckStatus,
    HypothesisAuthor,
    SourceType,
    validate_check_status,
    validate_source_type,
)


class AtomicFact(BaseModel):
    """
    분해의 최소 단위: 주체(subject) + 관측 가능한 상태 변화(state_change) + 시각.

    Provenance (Step 1):
      source_type — extracted | inferred | verified
      check_status — active | pending | promoted | dropped (고스트 A안)

    Neo4j :Fact 노드로 저장 시 위 필드 + trigger_event 포함.
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
    source_type: SourceType = Field(
        default=DEFAULT_SOURCE_TYPE,
        description="출처: extracted(원문) | inferred(몽상가) | verified(검색 검증).",
    )
    check_status: CheckStatus = Field(
        default=DEFAULT_CHECK_STATUS,
        description="검증 상태: active | pending | promoted | dropped(고스트).",
    )
    anchor_fact_id: str | None = Field(
        default=None,
        description=(
            "Dreamer 가설이 ripples from 한 completed_fact ID (inferred 전용). "
            "그래프: hover 시 원천→가설 점선. Neo4j: f.anchor_fact_id."
        ),
    )
    author: HypothesisAuthor | None = Field(
        default=None,
        description=(
            "가설 작성 주체. human=사용자 UI 입력, dreamer=Dreamer LLM, "
            "None=레거시(시각화·검증은 dreamer 와 동일 취급)."
        ),
    )
    stress_level: int = Field(
        default=0,
        ge=0,
        description=(
            "[STORM-S1-1] 누적 인과 스트레스. CAUSES 엣지마다 source provenance 가중치 합산."
        ),
    )
    is_critical: bool = Field(
        default=False,
        description="[STORM-S1-1] Perfect Storm 임계 돌파 시 Watcher가 True로 격상.",
    )
    source_file: str = Field(
        default="",
        description="Sprint 1 (C-2): ingest 파일명 또는 소스 label.",
    )
    page_range: str = Field(
        default="",
        description="Sprint 1 (C-2): PDF 페이지 범위 (예: p.1-3).",
    )
    chunk_id: str = Field(
        default="",
        description="Sprint 1 (C-2): ingest 청크 id (예: paper.pdf#chunk-2/5).",
    )

    @field_validator("source_type")
    @classmethod
    def validate_source_type_field(cls, value: str) -> str:
        """[PROV-S1-2] source_type 3값 강제."""
        return validate_source_type(value)

    @field_validator("check_status")
    @classmethod
    def validate_check_status_field(cls, value: str) -> str:
        """[PROV-S1-2] check_status 4값 강제."""
        return validate_check_status(value)

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
