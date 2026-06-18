"""Completed atomic facts section of the pipeline report.
파이프라인 리포트 — 완료된 원자 팩트 섹션.

Purpose / 목적
--------------
Lists facts in ``state['completed_facts']`` — atoms that passed verification
and left the deconstruct loop (accumulated via LangGraph ``operator.add``).
``state['completed_facts']`` 목록 — 검증 통과·deconstruct 루프를 벗어난 원자
(LangGraph ``operator.add``로 누적).

Pipeline position / 파이프라인 위치
-----------------------------------
After optional trace; before ``remaining`` section in ``compose``.
선택적 trace 이후; ``remaining`` 섹션 이전.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``completed_facts`` is append-only in the graph; order reflects completion time.
- Truncate long ``fact.id`` in display only (``[:8]``); never mutate models.
- Add fields only if ``AtomicFact`` schema exposes them for operators.
- 그래프에서 append-only; 순서 = 완료 시각 순.
- ``id`` 표시만 잘라내기; 모델 변경 금지.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_atomic_facts_section(state: State) -> list[str]:
    """Render completed atomic facts with optional reasoning lines."""
    lines = [f"--- ATOMIC FACTS ({len(state['completed_facts'])}) ---"]
    if not state["completed_facts"]:
        lines.append("  (none)")
        return lines

    for i, fact in enumerate(state["completed_facts"], 1):
        ts = fact.timestamp.isoformat() if fact.timestamp else "n/a"
        lines.append(f"  [{i}] id={fact.id[:8]}...")
        lines.append(f"      subject      : {fact.subject}")
        lines.append(f"      state_change : {fact.state_change}")
        lines.append(f"      is_atomic    : {fact.is_atomic}")
        lines.append(f"      timestamp    : {ts}")
        # Reasoning omitted when empty to keep report compact.
        # reasoning 비어 있으면 줄 생략.
        if fact.reasoning:
            lines.append(f"      reasoning    : {fact.reasoning}")
    return lines
