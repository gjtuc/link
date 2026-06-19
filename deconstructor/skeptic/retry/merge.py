"""
Merge first-pass and retry skeptic batch results.
1차 패스와 재시도 스케ptic 배치 결과 병합.

Purpose / 목적
--------------
Combine ``first`` and ``retry`` batch outputs without losing CORRELATION rejections
from the first pass or dropping newly verified edges from retry.
1차의 CORRELATION 거부를 유지하면서 재시도에서 새로 검증된 엣지를 반영한다.

Pipeline position / 파이프라인 위치
---------------------------------
  retry_inconclusive (after 2nd evaluate_batch)  →  **merge_retry_results**

When to modify / 수정 시점
--------------------------
- Pair identity is ``(source_fact_id, target_fact_id)`` ordered tuple throughout.
- CORRELATION from first pass always wins over retry for same pair.
- 동일 쌍에 1차 CORRELATION이 있으면 재시도 결과로 덮어쓰지 않음.

Key invariants / 핵심 불변조건
------------------------------
- ``retry_pairs`` = all pairs present in retry verdicts (full batch re-run).
- INCONCLUSIVE rejections in first pass for retried pairs are dropped.
- Verdict dict last-wins per pair from retry verdict list iteration order.
- 재시도 verdict가 동일 쌍의 1차 INCONCLUSIVE 거부를 대체.
"""

from __future__ import annotations

from deconstructor.skeptic.schemas import (
    CausalClassification,
    SkepticBatchResult,
)


def merge_retry_results(
    first: SkepticBatchResult,
    retry: SkepticBatchResult,
) -> SkepticBatchResult:
    """
    Replace INCONCLUSIVE rejections with retry verdicts; keep correlation rejects.
    INCONCLUSIVE 거부를 재시도 판정으로 교체; 상관 거부는 유지.

    Args:
        first: Initial skeptic batch before mechanism fill.
        retry: Second batch after mechanisms injected (full pairwise re-eval).

    Returns:
        Merged ``SkepticBatchResult`` with combined edges, rejections, verdicts.

    수정 시 주의점:
        ``kept_rejected`` logic is two-pass filter — test when changing classification rules.
        Verified edges from first pass preserved; retry adds new keys only.
    """
    retry_pairs = {
        (v.hypothesis.source_fact_id, v.hypothesis.target_fact_id)
        for v in retry.verdicts
    }

    # Keep first-pass rejects unless pair was retried AND not CORRELATION.
    kept_rejected = [
        r
        for r in first.rejected
        if (r.source_fact_id, r.target_fact_id) not in retry_pairs
        or r.classification == CausalClassification.CORRELATION
    ]

    retry_rejected = [
        r
        for r in retry.rejected
        if (r.source_fact_id, r.target_fact_id) in retry_pairs
    ]

    # Drop INCONCLUSIVE from first pass when retry produced a new verdict for that pair.
    kept_rejected = [
        r
        for r in kept_rejected
        if not (
            r.classification == CausalClassification.INCONCLUSIVE
            and (r.source_fact_id, r.target_fact_id) in retry_pairs
        )
    ]

    verified = list(first.verified_edges)
    seen = {(e.source_fact_id, e.target_fact_id) for e in verified}
    for edge in retry.verified_edges:
        key = (edge.source_fact_id, edge.target_fact_id)
        if key not in seen:
            verified.append(edge)
            seen.add(key)

    verdicts = list(first.verdicts)
    verdict_by_pair = {
        (v.hypothesis.source_fact_id, v.hypothesis.target_fact_id): v
        for v in verdicts
    }
    for v in retry.verdicts:
        verdict_by_pair[(v.hypothesis.source_fact_id, v.hypothesis.target_fact_id)] = v

    return SkepticBatchResult(
        verified_edges=verified,
        rejected=kept_rejected + retry_rejected,
        verdicts=list(verdict_by_pair.values()),
    )

