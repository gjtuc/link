"""Remaining non-atomic facts section — work queue at report time.
남은 비원자 팩트 섹션 — 리포트 시점 작업 큐.

Purpose / 목적
--------------
Shows ``state['extracted_facts']``: crumbs still awaiting decomposition or
stuck at depth cap (partial run). Empty list means null floor reached.
``state['extracted_facts']`` 표시: 아직 분해 대기 또는 깊이 상한에 걸린 조각.
비어 있으면 null floor 도달.

Pipeline position / 파이프라인 위치
-----------------------------------
Between atomic facts and verified edges in ``compose``.
``compose``에서 atomic facts와 verified edges 사이.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Pair with ``status.py`` and ``partial.py`` when changing incomplete semantics.
- One line per fact (compact); use ``atomic_facts`` section for full detail.
- 미완료 의미 변경 시 ``status.py``, ``partial.py`` 함께 수정.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_remaining_section(state: State) -> list[str]:
    """List non-atomic fragments still in extracted_facts."""
    remaining = state["extracted_facts"]
    lines = [f"--- REMAINING NON-ATOMIC ({len(remaining)}) ---"]
    if not remaining:
        lines.append("  (none - null floor reached or depth cap hit)")
        return lines

    for fact in remaining:
        lines.append(
            f"  - {fact.subject} | {fact.state_change} "
            f"(is_atomic={fact.is_atomic})"
        )
    return lines
