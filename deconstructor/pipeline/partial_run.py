"""Detect incomplete decomposition when depth cap leaves non-atomic crumbs.
깊이 상한에 비원자 조각이 남을 때 불완전 분해 감지.

Purpose / 목적
--------------
``detect_partial_run`` implements mechanical P9 rules: partial when
``recursion_depth >= max_recursion_depth`` AND ``extracted_facts`` non-empty;
otherwise decomposition reached null floor (not partial).
기계적 P9 규칙: ``recursion_depth >= max_recursion_depth`` 이고
``extracted_facts`` 비어 있지 않으면 partial; 아니면 null floor(비-partial).

Pipeline position / 파이프라인 위치
-----------------------------------
Called from graph nodes (typically end of deconstruct loop) to set
``state['partial_run']`` and ``partial_run_reason`` before weaver/report.
deconstruct 루프 끝 등 그래프 노드에서 호출 → weaver/report 전
``partial_run`` / ``partial_run_reason`` 설정.

Reason codes / 사유 코드
------------------------
- ``REASON_DEPTH_CAP`` (``depth_cap_non_atomic_remain``): cap hit with leftovers.
- ``REASON_COMPLETE`` (``""``): successful completion.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Keep ``PartialRunInfo`` frozen; use new reason constants for new failure modes.
- Display layer duplicates logic in ``report.sections.status`` — sync both.
- ``PartialRunInfo`` frozen 유지; 새 실패 모드는 새 reason 상수.
- ``report.sections.status``와 의미 동기화.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Canonical reason codes for partial runs (machine-readable).
# 부분 실행 기계 readable 사유 코드.
REASON_DEPTH_CAP = "depth_cap_non_atomic_remain"
REASON_COMPLETE = ""


class PartialRunInfo(BaseModel):
    """Mechanical status of the deconstruct-verify loop.
    deconstruct-verify 루프의 기계적 상태."""

    partial_run: bool = Field(
        description="True when decomposition ended before null floor.",
    )
    reason: str = Field(
        default="",
        description="Machine-readable reason code when partial_run is True.",
    )
    non_atomic_count: int = 0
    completed_atomic_count: int = 0
    recursion_depth: int = 0
    max_recursion_depth: int = 0

    model_config = {"frozen": True}


def detect_partial_run(
    *,
    extracted_facts: list,
    completed_facts: list,
    recursion_depth: int,
    max_recursion_depth: int,
) -> PartialRunInfo:
    """
    Step P9-1: depth cap reached while non-atomic crumbs remain.
    Step P9-2: otherwise decomposition reached null floor (not partial).

    P9-1: 상한 도달 + 비원자 조각 잔존 → partial.
    P9-2: 그 외 → null floor (partial 아님).
    """
    non_atomic_count = len(extracted_facts)
    at_cap = recursion_depth >= max_recursion_depth
    partial = non_atomic_count > 0 and at_cap

    return PartialRunInfo(
        partial_run=partial,
        reason=REASON_DEPTH_CAP if partial else REASON_COMPLETE,
        non_atomic_count=non_atomic_count,
        completed_atomic_count=len(completed_facts),
        recursion_depth=recursion_depth,
        max_recursion_depth=max_recursion_depth,
    )
