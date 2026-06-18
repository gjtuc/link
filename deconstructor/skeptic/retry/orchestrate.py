"""
Orchestrate INCONCLUSIVE hypothesis retry.
INCONCLUSIVE 가설 재시도 오케스트레이션.

Purpose / 목적
--------------
Second skeptic pass: filter INCONCLUSIVE rejections from first batch, fill
``proposed_mechanism`` (stub or LLM), re-run ``evaluate_batch`` on full fact set
with mechanism map, merge into first-pass result.
1차 배치에서 INCONCLUSIVE만 골라 메커니즘 채운 뒤 전체 사실 집합을 재평가하고
1차 결과와 병합한다.

Pipeline position / 파이프라인 위치
---------------------------------
  SkepticEngine.evaluate_batch (1st)  →  **retry_inconclusive**  →  skeptic_node state

When to modify / 수정 시점
--------------------------
- Retry eligibility: only ``CausalClassification.INCONCLUSIVE`` in ``first_pass.rejected``.
- ``dry_run=True`` default matches node — live LLM requires ``dry_run=False``.
- 재시도 대상 분류 변경 시 merge.py 정책과 함께 검토.

Key invariants / 핵심 불변조건
------------------------------
- Re-evaluation uses full ``facts`` list + ``mechanisms`` map — not subset of pairs only.
- Empty proposals → first_pass unchanged, RETRY_SKIP logged.
- 제안 없으면 1차 결과 그대로, RETRY_SKIP 로그.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.skeptic.engine import SkepticEngine
from deconstructor.skeptic.mechanism_proposal import (
    fill_mechanisms,
    proposals_to_mechanism_map,
)
from deconstructor.skeptic.retry.merge import merge_retry_results
from deconstructor.skeptic.run_log import SkepticLogEntry
from deconstructor.skeptic.schemas import CausalClassification, SkepticBatchResult


def retry_inconclusive(
    engine: SkepticEngine,
    facts: list[AtomicFact],
    first_pass: SkepticBatchResult,
    *,
    dry_run: bool = True,
) -> tuple[SkepticBatchResult, list[SkepticLogEntry]]:
    """
    S4-1: find INCONCLUSIVE rejections.
    S4-2: propose mechanisms (stub in dry_run).
    S4-3: re-evaluate only those pairs.
    S4-4: merge into first pass result.

    INCONCLUSIVE 거부 탐색 → 메커니즘 제안 → 해당 쌍 재평가 → 1차 결과 병합.

    Args:
        engine: Shared ``SkepticEngine`` instance (same rules as first pass).
        facts: Complete atomic fact list from pipeline.
        first_pass: Initial ``evaluate_batch`` result before retry.
        dry_run: Use stub mechanisms when True; LLM when False.

    Returns:
        Tuple of (merged batch result, retry-specific log entries).

    수정 시 주의점:
        ``retry_batch`` re-evaluates ALL pairs but merge only overlays retried pairs.
        Mechanism map keys must be ordered (source_id, target_id).
    """
    log: list[SkepticLogEntry] = []
    inconclusive = [
        r for r in first_pass.rejected
        if r.classification == CausalClassification.INCONCLUSIVE
    ]

    if not inconclusive:
        log.append(
            SkepticLogEntry(
                level="INFO",
                code="RETRY_SKIP",
                message="no inconclusive hypotheses to retry",
            )
        )
        return first_pass, log

    facts_index = {f.id: f for f in facts}
    proposals = fill_mechanisms(
        first_pass.rejected, facts_index, dry_run=dry_run
    )

    if not proposals.proposals:
        log.append(
            SkepticLogEntry(
                level="INFO",
                code="RETRY_SKIP",
                message="no mechanism proposals generated",
            )
        )
        return first_pass, log

    mech_map = proposals_to_mechanism_map(proposals)
    log.append(
        SkepticLogEntry(
            level="INFO",
            code="RETRY_START",
            message=f"retrying {len(proposals.proposals)} inconclusive pair(s)",
        )
    )

    # Full batch re-run: mechanisms attach only to keys present in mech_map.
    retry_batch = engine.evaluate_batch(facts, mechanisms=mech_map)
    merged = merge_retry_results(first_pass, retry_batch)

    newly_verified = len(retry_batch.verified_edges)
    log.append(
        SkepticLogEntry(
            level="INFO",
            code="RETRY_DONE",
            message=f"retry verified {newly_verified} edge(s)",
        )
    )

    return merged, log
