"""
Mechanism proposal schemas.
메커니즘 제안 스키마.

Purpose / 목적
--------------
Pydantic models for LLM structured output and batch transport between fill/retry/engine.
LLM 구조화 출력 및 fill·retry·engine 간 배치 전달용 Pydantic 모델.

Pipeline position / 파이프라인 위치
---------------------------------
  mechanism_proposal.*  ↔  engine ``mechanisms`` map (via fill.proposals_to_mechanism_map)

When to modify / 수정 시점
--------------------------
- ``proposed_mechanism`` min_length=1 — empty strings fail validation before retry.
- Extra metadata fields require updating LLM structured output binding.

Key invariants / 핵심 불변조건
------------------------------
- Ordered pair ids match ``CausalHypothesis`` source/target fact ids.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MechanismProposal(BaseModel):
    """
    One directed mechanism proposal for a fact pair.
    사실 쌍 하나에 대한 방향성 메커니즘 제안.

    수정 시 주의점:
        LLM may return ids — ``llm.invoke_mechanism_proposal`` overwrites from facts.
    """

    source_fact_id: str
    target_fact_id: str
    proposed_mechanism: str = Field(min_length=1)


class MechanismProposalBatch(BaseModel):
    """
    Collection of proposals from one fill pass.
    한 번의 fill 패스에서 나온 제안 모음.
    """

    proposals: list[MechanismProposal] = Field(default_factory=list)
