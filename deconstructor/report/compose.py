"""Compose full pipeline report from ordered section formatters.
섹션 포맷터를 순서대로 이어 전체 파이프라인 리포트를 조립.

Purpose / 목적
--------------
``format_dry_run_report`` stitches header, status, optional trace, facts,
edges, skeptic output, partial-run banner, weaver summary, and footer into
one newline-joined string suitable for stdout or log files.
``format_dry_run_report``가 헤더·상태·(선택) 추적·팩트·엣지·스켉틱·
부분 실행·위버·푸터를 하나의 줄바꿈 문자열로 조립합니다.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    run_pipeline_traced() --> TracedRun
        |
        v
    format_traced_report(traced)  --calls-->  format_dry_run_report(state, steps=...)

``format_traced_report`` is a one-line wrapper; all section ordering lives here.
``format_traced_report``는 래퍼이며 **섹션 순서의 단일 진실 공급원**은 이 파일입니다.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- To add/remove/reorder sections: edit ``format_dry_run_report`` only; keep
  ``format_traced_report`` as ``final_state + steps`` passthrough.
- Pass ``steps=None`` to omit trace block (state-only reports).
- Section functions return ``list[str]`` or ``str``; use ``extend`` vs ``append``
  consistently — blank lines between major blocks are intentional readability.
- **섹션 추가/삭제/순서:** ``format_dry_run_report``만 수정.
- 추적 생략: ``steps=None``.
- 섹션 간 빈 줄은 가독성용 — 제거 시 CLI 레이아웃 깨짐 주의.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State
from deconstructor.pipeline_trace import StepRecord, TracedRun
from deconstructor.report.sections.atomic_facts import format_atomic_facts_section
from deconstructor.report.sections.edges import format_edges_section
from deconstructor.report.sections.footer import format_footer_section
from deconstructor.report.sections.header import format_header_section
from deconstructor.report.sections.partial import format_partial_run_section
from deconstructor.report.sections.rejected import format_rejected_section
from deconstructor.report.sections.remaining import format_remaining_section
from deconstructor.report.sections.skeptic_log import format_skeptic_log_section
from deconstructor.report.sections.status import format_status_line
from deconstructor.report.sections.trace import format_step_trace
from deconstructor.report.sections.weaver import format_weaver_section


def format_dry_run_report(
    state: State,
    *,
    steps: list[StepRecord] | None = None,
) -> str:
    """Assemble all report sections in canonical display order.
    표시 순서에 맞춰 모든 리포트 섹션을 조립."""
    lines: list[str] = []

    # Block 1: metadata header + single-line decomposition status.
    # 블록 1: 메타데이터 헤더 + 분해 상태 한 줄.
    lines.extend(format_header_section(state))
    lines.append(format_status_line(state))
    lines.append("")

    # Optional trace: only when caller supplies StepRecord list from traced run.
    # 선택적 추적: traced run에서 StepRecord 목록을 넘긴 경우만.
    if steps:
        lines.append(format_step_trace(steps))
        lines.append("")

    # Core decomposition artifacts (facts still in flight vs completed).
    # 핵심 분해 산출물 (진행 중 vs 완료 팩트).
    lines.extend(format_atomic_facts_section(state))
    lines.append("")
    lines.extend(format_remaining_section(state))
    lines.append("")

    # Causal graph outputs from verify/skeptic stages.
    # verify/skeptic 단계의 인과 그래프 결과.
    lines.extend(format_edges_section(state))
    lines.append("")
    lines.extend(format_rejected_section(state))
    lines.append("")
    lines.extend(format_skeptic_log_section(state))
    lines.append("")

    # Partial run is omitted entirely when state.partial_run is falsy.
    # partial_run이 False면 섹션 자체를 생략.
    partial = format_partial_run_section(state)
    if partial:
        lines.extend(partial)
        lines.append("")

    # Weaver persistence summary (last pipeline node).
    # 위버 영속화 요약 (파이프라인 마지막 노드).
    lines.extend(format_weaver_section(state))
    lines.append("")
    lines.extend(format_footer_section(state))

    return "\n".join(lines)


def format_traced_report(traced: TracedRun) -> str:
    """Convenience: report from TracedRun without unpacking fields manually.
    TracedRun에서 final_state와 steps를 수동 분해 없이 리포트 생성."""
    return format_dry_run_report(traced.final_state, steps=traced.steps)
