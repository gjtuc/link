"""Report header section — input metadata and depth caps.
리포트 헤더 섹션 — 입력 메타데이터 및 깊이 상한.

Purpose / 목적
--------------
Renders the top banner: raw input text, number of deconstruct passes completed,
and configured ``max_recursion_depth`` cap from State.
상단 배너: 원문 입력, 완료된 deconstruct 패스 수, State의 ``max_recursion_depth`` 상한.

Pipeline position / 파이프라인 위치
-----------------------------------
First block in ``compose.format_dry_run_report`` (before STATUS line).
``compose.format_dry_run_report`` **첫 블록** (STATUS 줄 이전).

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Add new metadata fields only if they exist on ``State`` at report time.
- Keep label column width (~10 chars) aligned with other sections for scanability.
- Use ``SEP`` from ``_constants`` for banner lines.
- ``State``에 실제 존재하는 필드만 추가.
- 라벨 열 너비(~10자) 다른 섹션과 맞출 것.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State
from deconstructor.report.sections._constants import SEP


def format_header_section(state: State) -> list[str]:
    """Return banner + INPUT/LOOPS/DEPTH CAP lines (no trailing blank line).
    배너 + INPUT/LOOPS/DEPTH CAP 줄 반환 (끝 빈 줄 없음)."""
    return [
        SEP,
        "  DECONSTRUCTOR - PIPELINE REPORT",
        SEP,
        "",
        f"INPUT     : {state['raw_text']}",
        # recursion_depth counts completed deconstruct loop iterations.
        # recursion_depth = 완료된 deconstruct 루프 반복 횟수.
        f"LOOPS     : {state['recursion_depth']} deconstruct pass(es)",
        f"DEPTH CAP : {state['max_recursion_depth']}",
    ]
