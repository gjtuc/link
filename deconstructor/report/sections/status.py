"""Report decomposition status line — COMPLETE / IN PROGRESS / INCOMPLETE.
리포트 분해 상태 한 줄 — COMPLETE / IN PROGRESS / INCOMPLETE.

Purpose / 목적
--------------
Derives a single human-readable STATUS from ``extracted_facts``,
``recursion_depth``, and ``max_recursion_depth`` without re-running
``detect_partial_run`` (mirrors its depth-cap semantics for display).
``extracted_facts``, ``recursion_depth``, ``max_recursion_depth``만으로
사람이 읽을 STATUS 한 줄을 도출 (``detect_partial_run`` 재실행 없이,
깊이 상한 의미는 동일).

Pipeline position / 파이프라인 위치
-----------------------------------
Immediately after header in ``compose.format_dry_run_report``.
헤더 직후 ``compose``에서 삽입.

Status semantics / 상태 의미
----------------------------
- **INCOMPLETE**: non-atomic crumbs remain AND depth cap reached.
- **COMPLETE**: ``extracted_facts`` empty (null floor).
- **IN PROGRESS**: crumbs remain but cap not yet hit (mid-run snapshots only).
- **INCOMPLETE**: 비원자 조각 남음 + 깊이 상한 도달.
- **COMPLETE**: ``extracted_facts`` 비움 (null floor).
- **IN PROGRESS**: 조각 남음, 상한 미도달 (중간 스냅샷용).

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Keep logic aligned with ``pipeline.partial_run.detect_partial_run``; if one
  changes, update the other and report section ``partial.py``.
- Return a single ``str`` (not list) — compose uses ``lines.append``.
- ``detect_partial_run``과 의미 동기화; 변경 시 ``partial.py``도 검토.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_status_line(state: State) -> str:
    """One-line STATUS summary for the report header area."""
    # INCOMPLETE: same condition as PartialRunInfo.partial_run (display layer).
    # INCOMPLETE: PartialRunInfo.partial_run 과 동일 조건 (표시 계층).
    incomplete = bool(state["extracted_facts"]) and (
        state["recursion_depth"] >= state["max_recursion_depth"]
    )
    if incomplete:
        return (
            f"STATUS    : INCOMPLETE - depth cap hit with "
            f"{len(state['extracted_facts'])} non-atomic fragment(s)"
        )
    # Null floor: nothing left to decompose.
    # Null floor: 더 분해할 조각 없음.
    if not state["extracted_facts"]:
        return "STATUS    : COMPLETE - null floor reached"
    return "STATUS    : IN PROGRESS - non-atomic fragments remain"
