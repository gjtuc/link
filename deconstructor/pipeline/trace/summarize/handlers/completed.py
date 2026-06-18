"""Trace detail and count helpers for completed_facts reducer updates.
completed_facts reducer update용 trace detail·카운트 헬퍼.

Purpose / 목적
--------------
LangGraph appends to ``completed_facts`` via ``operator.add``; each update
carries only **new** atoms. Handlers report ``completed+=N`` in detail.
``operator.add``로 ``completed_facts`` 누적; update에는 **신규** 원자만 포함.
detail에 ``completed+=N`` 표기.

Pipeline position / 파이프라인 위치
-----------------------------------
Second handler; typically follows verify node passing atoms to completed pile.
두 번째 핸들러; verify가 completed로 넘길 때.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``count_completed_facts`` returns len of **this update's** list, not total state.
- 이번 update 리스트 길이만 반환 (state 전체 completed 수 아님).
"""

from __future__ import annotations

from typing import Any


def detail_completed_facts(update: dict[str, Any]) -> str | None:
    """Show how many facts completed in this update."""
    if "completed_facts" not in update:
        return None
    return f"completed+={len(update['completed_facts'])}"


def count_completed_facts(update: dict[str, Any]) -> int | None:
    """Batch completion count for StepRecord.completed_count."""
    if "completed_facts" not in update:
        return None
    return len(update["completed_facts"])
