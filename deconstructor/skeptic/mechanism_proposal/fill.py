"""
Fill mechanisms for inconclusive rejections — stub or LLM.
미결정 거부에 메커니즘 채우기 — 스텁 또는 LLM.

Purpose / 목적
--------------
Produce ``MechanismProposalBatch`` for INCONCLUSIVE pairs so R06/R07 can PASS
on retry. Dispatches to deterministic stub (dry_run) or live LLM.
INCONCLUSIVE 쌍에 ``MechanismProposalBatch``를 생성해 재시도 시 R06/R07 통과 가능하게 함.
dry_run이면 스텁, 아니면 LLM.

Pipeline position / 파이프라인 위치
---------------------------------
  retry.orchestrate  →  **fill_mechanisms**  →  proposals_to_mechanism_map  →  engine

When to modify / 수정 시점
--------------------------
- Filtering: only ``CausalClassification.INCONCLUSIVE`` in rejected list.
- Missing fact ids in index → pair skipped silently (no proposal).
- INCONCLUSIVE만 대상; 인덱스에 없는 fact id는 조용히 스킵.

Key invariants / 핵심 불변조건
------------------------------
- ``proposals_to_mechanism_map`` keys are ordered (source_id, target_id).
- Empty pairs list → empty ``MechanismProposalBatch``, not error.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.skeptic.mechanism_proposal.llm import propose_mechanisms_llm
from deconstructor.skeptic.mechanism_proposal.schemas import MechanismProposalBatch
from deconstructor.skeptic.mechanism_proposal.stub import stub_mechanism
from deconstructor.skeptic.schemas import CausalClassification


def proposals_for_inconclusive_stub(
    rejected: list,
    facts_by_id: dict[str, AtomicFact],
) -> MechanismProposalBatch:
    """
    R14-1a: dry-run stub proposals.
    R14-1a: 드라이런 스텁 제안.

    Args:
        rejected: ``RejectedHypothesis`` list from first skeptic pass.
        facts_by_id: Fact id index for subject/state_change lookup.

    Returns:
        Batch of stub mechanism strings for each INCONCLUSIVE pair with valid facts.

    수정 시 주의점:
        CORRELATION rows ignored — retry must not override correlation rejects.
    """
    from deconstructor.skeptic.mechanism_proposal.schemas import MechanismProposal

    proposals = []
    for rej in rejected:
        if rej.classification != CausalClassification.INCONCLUSIVE:
            continue
        src = facts_by_id.get(rej.source_fact_id)
        tgt = facts_by_id.get(rej.target_fact_id)
        if src is None or tgt is None:
            continue
        proposals.append(
            MechanismProposal(
                source_fact_id=rej.source_fact_id,
                target_fact_id=rej.target_fact_id,
                proposed_mechanism=stub_mechanism(src, tgt),
            )
        )
    return MechanismProposalBatch(proposals=proposals)


def fill_mechanisms(
    rejected: list,
    facts_by_id: dict[str, AtomicFact],
    *,
    dry_run: bool = True,
    llm=None,
) -> MechanismProposalBatch:
    """
    R14-1: dispatch stub vs LLM mechanism fill.
    R14-1: 스텁 vs LLM 메커니즘 채우기 분기.

    Args:
        rejected: First-pass rejection list.
        facts_by_id: Atomic facts by id.
        dry_run: True → ``proposals_for_inconclusive_stub``; False → LLM batch.
        llm: Optional injectable chat model (tests); None → ``get_chat_model()``.

    Returns:
        ``MechanismProposalBatch`` (possibly empty).

    수정 시 주의점:
        LLM path builds pairs list then calls ``propose_mechanisms_llm`` — network cost
        scales with INCONCLUSIVE count, not n².
    """
    if dry_run:
        return proposals_for_inconclusive_stub(rejected, facts_by_id)

    pairs: list[tuple[AtomicFact, AtomicFact]] = []
    for rej in rejected:
        if rej.classification != CausalClassification.INCONCLUSIVE:
            continue
        src = facts_by_id.get(rej.source_fact_id)
        tgt = facts_by_id.get(rej.target_fact_id)
        if src and tgt:
            pairs.append((src, tgt))

    if not pairs:
        return MechanismProposalBatch()

    return propose_mechanisms_llm(pairs, llm=llm)


def proposals_to_mechanism_map(
    batch: MechanismProposalBatch,
) -> dict[tuple[str, str], str]:
    """
    Convert proposal batch to engine ``mechanisms`` argument shape.
    제안 배치를 엔진 ``mechanisms`` 인자 형태로 변환.

    Args:
        batch: LLM or stub proposal batch.

    Returns:
        Dict ``(source_fact_id, target_fact_id) -> proposed_mechanism``.

    수정 시 주의점:
        Duplicate pairs in batch: last proposal wins (should not occur).
    """
    return {
        (p.source_fact_id, p.target_fact_id): p.proposed_mechanism
        for p in batch.proposals
    }
