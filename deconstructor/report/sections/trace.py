"""Pipeline trace section — per-node StepRecord timeline.
파이프라인 추적 섹션 — 노드별 StepRecord 타임라인.

Purpose / 목적
--------------
Formats the list of ``StepRecord`` objects produced by
``run_pipeline_traced`` into a fixed-width console block showing step index,
node name, compact detail string, and full node sequence.
``run_pipeline_traced``가 만든 ``StepRecord`` 목록을 단계 번호·노드명·
요약 detail·전체 시퀀스로 포맷.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    graph.stream(updates) --> summarize_update --> StepRecord[]
        --> format_step_trace(steps)   [optional block in compose]

Omitted from report when ``compose.format_dry_run_report(..., steps=None)``.
``steps=None``이면 compose에서 이 블록 생략.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Detail strings are built in ``pipeline/trace/summarize``; change formatting
  here only for layout (padding, labels), not field extraction.
- ``step_index`` is 1-based in display (set in ``trace/runner.py``).
- detail 내용은 ``pipeline/trace/summarize``; 여기서는 레이아웃만.
- 화면 ``step_index``는 1부터 (runner에서 설정).
"""

from __future__ import annotations

from deconstructor.pipeline_trace import StepRecord


def format_step_trace(steps: list[StepRecord]) -> str:
    """Format step list as multi-line string (includes section header).
    단계 목록을 여러 줄 문자열로 (섹션 헤더 포함)."""
    lines = ["--- PIPELINE TRACE ---"]
    if not steps:
        lines.append("  (no steps recorded)")
        return "\n".join(lines)

    for step in steps:
        # :02d index, :<12 node name column for alignment with legacy output.
        # :02d 인덱스, :<12 노드명 열 정렬.
        lines.append(f"  [{step.step_index:02d}] {step.node:<12} {step.detail}")
    # Arrow chain helps spot unexpected routing (e.g. extra deconstruct loops).
    # 화살표 체인으로 비정상 라우팅(추가 deconstruct 루프 등) 확인.
    lines.append(f"  sequence: {' -> '.join(s.node for s in steps)}")
    return "\n".join(lines)
