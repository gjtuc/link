"""
LLM mechanism proposal — testable with mock LLM.
LLM 메커니즘 제안 — mock LLM으로 테스트 가능.

Purpose / 목적
--------------
Invoke structured chat model to produce one-sentence mechanical propagation paths
between atomic fact pairs for INCONCLUSIVE retry.
구조화 채팅 모델로 원자 사실 쌍 간 기계적 전파 경로(한 문장)를 생성 — INCONCLUSIVE 재시도용.

Pipeline position / 파이프라인 위치
---------------------------------
  fill_mechanisms (dry_run=False)  →  **propose_mechanisms_llm**  →  mechanism map

When to modify / 수정 시점
--------------------------
- Prompt changes: edit ``prompts.py`` — keep structured output schema stable.
- ``invoke_mechanism_proposal`` re-binds fact ids from inputs (LLM may omit/wrong ids).
- 프롬프트는 ``prompts.py``; fact id는 입력에서 재바인딩 유지.

Key invariants / 핵심 불변조건
------------------------------
- Returns ``MechanismProposal`` with non-empty ``proposed_mechanism`` (schema min_length=1).
- Injectable ``llm`` bypasses ``get_chat_model()`` for unit tests.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.llm import get_chat_model
from deconstructor.models import AtomicFact
from deconstructor.skeptic.mechanism_proposal.prompts import (
    MECHANISM_SYSTEM,
    MECHANISM_USER,
)
from deconstructor.skeptic.mechanism_proposal.schemas import (
    MechanismProposal,
    MechanismProposalBatch,
)


def build_mechanism_messages(source: AtomicFact, target: AtomicFact) -> list:
    """
    Build LangChain message list for one mechanism proposal call.
    단일 메커니즘 제안 호출용 LangChain 메시지 리스트 생성.

    Args:
        source: Hypothesized cause crumb.
        target: Hypothesized effect crumb.

    Returns:
        [SystemMessage, HumanMessage] with formatted subjects and state changes.

    수정 시 주의점:
        Template placeholders must match ``MECHANISM_USER`` in prompts.py.
    """
    return [
        SystemMessage(content=MECHANISM_SYSTEM),
        HumanMessage(
            content=MECHANISM_USER.format(
                source_subject=source.subject,
                source_change=source.state_change,
                target_subject=target.subject,
                target_change=target.state_change,
            )
        ),
    ]


def invoke_mechanism_proposal(
    source: AtomicFact,
    target: AtomicFact,
    *,
    llm: Any | None = None,
) -> MechanismProposal:
    """
    R14-2: structured single-pair mechanism proposal.
    R14-2: 구조화 단일 쌍 메커니즘 제안.

    Args:
        source: Cause fact.
        target: Effect fact.
        llm: Optional model with ``invoke`` + structured output; None → default chat model.

    Returns:
        ``MechanismProposal`` with ids from input facts (not LLM output ids).

    수정 시 주의점:
        Always overwrite source/target ids from ``AtomicFact`` — prevents LLM id drift.
    """
    model = (
        llm
        if llm is not None
        else get_chat_model().with_structured_output(MechanismProposal)
    )
    proposal: MechanismProposal = model.invoke(
        build_mechanism_messages(source, target)
    )
    return MechanismProposal(
        source_fact_id=source.id,
        target_fact_id=target.id,
        proposed_mechanism=proposal.proposed_mechanism,
    )


def propose_mechanisms_llm(
    pairs: list[tuple[AtomicFact, AtomicFact]],
    *,
    llm: Any | None = None,
) -> MechanismProposalBatch:
    """
    R14-3: batch LLM proposals for inconclusive pairs.
    R14-3: 미결정 쌍에 대한 LLM 배치 제안.

    Args:
        pairs: Ordered (source, target) fact tuples.
        llm: Shared injectable model for all pairs in batch.

    Returns:
        ``MechanismProposalBatch`` with one proposal per pair (sequential calls).

    수정 시 주의점:
        Sequential invoke — parallelization would need rate-limit and ordering policy.
    """
    proposals = [
        invoke_mechanism_proposal(src, tgt, llm=llm) for src, tgt in pairs
    ]
    return MechanismProposalBatch(proposals=proposals)

