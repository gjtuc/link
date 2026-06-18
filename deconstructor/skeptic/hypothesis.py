"""
Generate candidate causal hypotheses from a set of atomic facts.
원자 사실 집합에서 후보 인과 가설을 생성한다.

Purpose / 목적
--------------
Step 1 of skeptic: enumerate every ordered pair (A → B) where A ≠ B, optionally
attaching proposed mechanism text per pair.
스케ptic 1단계: A ≠ B인 모든 순서쌍 (A → B)을 열거하고, 쌍별로 제안 메커니즘 문구를
선택적으로 붙인다.

Pipeline position / 파이프라인 위치
---------------------------------
  completed_facts  →  **generate_pairwise_hypotheses**  →  SkepticEngine.evaluate_*

When to modify / 수정 시점
--------------------------
- Changing pair enumeration (e.g. skip distant pairs): affects batch size O(n²).
- Mechanism map keying must stay ``(source_id, target_id)`` ordered — retry merge
  depends on this convention.
- 쌍 열거 방식 변경 시 배치 크기 O(n²)에 영향. 메커니즘 맵 키는 순서쌍 방향 유지.

Key invariants / 핵심 불변조건
------------------------------
- Self-pairs (same id) are never emitted.
- ``len(facts) < 2`` → empty list (no hypotheses).
- ``facts_by_id`` last-wins on duplicate ids — upstream must ensure unique ids.
- 동일 id 자기쌍은 생성하지 않음. 사실 2개 미만이면 빈 리스트.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.skeptic.schemas import CausalHypothesis


def generate_pairwise_hypotheses(
    facts: list[AtomicFact],
    *,
    mechanisms: dict[tuple[str, str], str] | None = None,
) -> list[CausalHypothesis]:
    """
    Build one ``CausalHypothesis`` per ordered fact pair.
    순서가 있는 사실 쌍마다 ``CausalHypothesis`` 하나를 만든다.

    Args:
        facts: Atomic crumbs to link.
        mechanisms: Optional map ``(source_id, target_id) -> mechanism text``.
            Missing keys default to empty ``proposed_mechanism``.

    Returns:
        List of length ``n * (n - 1)`` for n = len(facts), or [] if n < 2.

    수정 시 주의점:
        Double loop order (outer source, inner target) defines stable hypothesis
        ordering for tests and reports — change only with fixture updates.
    """
    if len(facts) < 2:
        return []

    mech = mechanisms or {}
    hypotheses: list[CausalHypothesis] = []

    for source in facts:
        for target in facts:
            if source.id == target.id:
                continue  # R01 would reject anyway; omit at generation time.
            key = (source.id, target.id)
            hypotheses.append(
                CausalHypothesis(
                    source_fact_id=source.id,
                    target_fact_id=target.id,
                    proposed_mechanism=mech.get(key, ""),
                )
            )

    return hypotheses


def facts_by_id(facts: list[AtomicFact]) -> dict[str, AtomicFact]:
    """
    Index facts for O(1) lookup during rule evaluation.
    규칙 평가 중 O(1) 조회를 위한 사실 인덱스.

    Args:
        facts: List of atomic facts (ids should be unique).

    Returns:
        Dict mapping fact id → ``AtomicFact``.

    수정 시 주의점:
        Duplicate ids silently overwrite — validate upstream in pipeline, not here.
    """
    return {f.id: f for f in facts}
