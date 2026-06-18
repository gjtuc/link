"""Trace detail and count helpers for verified_edges updates.
verified_edges update용 trace detail·카운트 헬퍼.

Purpose / 목적
--------------
``detail_verified_edges`` logs edge list length; ``count_verified_edges`` feeds
``StepRecord.verified_edge_count`` for test assertions.
``detail_verified_edges``는 엣지 개수 로그; ``count_verified_edges``는
``StepRecord.verified_edge_count`` 테스트 검증용.

Pipeline position / 파이프라인 위치
-----------------------------------
After completed_facts handler; reflects verify/skeptic edge approval batches.
completed_facts 다음; verify/skeptic 엣지 승인 배치 반영.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Count uses ``len(update['verified_edges'])`` on the **delta** list in update,
  not cumulative graph state — matches LangGraph update semantics.
- update의 **delta** 리스트 길이 사용 (누적 state 전체 아님).
"""

from __future__ import annotations

from typing import Any


def detail_verified_edges(update: dict[str, Any]) -> str | None:
    """Log count of edges in this update batch."""
    if "verified_edges" not in update:
        return None
    return f"edges={len(update['verified_edges'])}"


def count_verified_edges(update: dict[str, Any]) -> int | None:
    """Return batch edge count for StepRecord.verified_edge_count."""
    if "verified_edges" not in update:
        return None
    return len(update["verified_edges"])
