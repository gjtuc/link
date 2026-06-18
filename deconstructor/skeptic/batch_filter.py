"""
Batch-level edge conflict resolution.
배치 수준 엣지 충돌 해소.

Purpose / 목적
--------------
Rule 12 (batch): when both A→B and B→A pass per-hypothesis checks, keep a single
direction per unordered pair — the edge with higher ``probability``.
규칙 12(배치): A→B와 B→A가 모두 통과하면 무방향 쌍당 하나의 방향만 유지 —
``probability``가 더 높은 엣지를 남긴다.

Pipeline position / 파이프라인 위치
---------------------------------
  SkepticEngine.evaluate_batch (post per-pair evaluation)  →  **resolve_bidirectional_conflicts**

When to modify / 수정 시점
--------------------------
- Tie-breaking when probabilities equal: currently last-seen wins in iteration order.
- Alternative policies (latency, rule count) belong here, not in per-pair rules.
- 동률 시 현재는 순회 순서상 마지막 엣지가 이김 — 정책 변경 시 테스트 갱신.

Key invariants / 핵심 불변조건
------------------------------
- Input/output are lists of ``CausalEdge``; order after dedup is non-deterministic
  (dict values). Downstream should not rely on edge list order.
- Only verified (accepted) edges enter this function — rejected pairs are ignored.
- 출력 순서는 보장되지 않음. 거부된 쌍은 이 단계에 들어오지 않음.
"""

from __future__ import annotations

from deconstructor.models import CausalEdge


def resolve_bidirectional_conflicts(edges: list[CausalEdge]) -> list[CausalEdge]:
    """
    Rule 12 (batch) - keep single direction per unordered pair.
    규칙 12(배치) — 무방향 쌍당 단일 방향만 유지.

    When A->B and B->A both survive rule checks, retain higher probability.
    A→B와 B→A가 모두 남으면 probability가 더 큰 쪽을 유지.

    Args:
        edges: Accepted causal edges from one batch pass (may include reverse pairs).

    Returns:
        Deduplicated edge list with at most one directed edge per fact-id pair.

    수정 시 주의점:
        ``frozenset`` keys treat (A,B) and (B,A) as identical — intentional.
        Equal probability: later edge in input list overwrites earlier in ``best`` map.
    """
    best: dict[frozenset[str], CausalEdge] = {}

    for edge in edges:
        key = frozenset({edge.source_fact_id, edge.target_fact_id})
        current = best.get(key)
        if current is None or edge.probability > current.probability:
            best[key] = edge

    return list(best.values())
