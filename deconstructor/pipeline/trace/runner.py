"""Run pipeline with LangGraph stream tracing and final invoke.
LangGraph stream 추적 및 최종 invoke로 파이프라인 실행.

Purpose / 목적
--------------
``run_pipeline_traced`` executes the compiled graph twice in spirit: once with
``stream_mode="updates"`` to record per-node deltas as ``StepRecord`` list,
then ``invoke`` for authoritative ``final_state`` (stream and invoke may differ
slightly in timing but should match terminal state).
컴파일 그래프 실행: ``stream_mode="updates"``로 노드별 ``StepRecord`` 수집 후
``invoke``로 권위 있는 ``final_state`` 확보.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    make_initial_state --> build_graph(dry_run, persist_db)
        --> stream(updates) + summarize_update --> steps[]
        --> invoke --> TracedRun(final_state, steps)

Entry point for CLI dry-run and integration tests needing step timelines.
CLI dry-run·단계 타임라인이 필요한 통합 테스트 진입점.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``dry_run=True``, ``persist_db=False`` defaults match local dev safety.
- ``step_index`` assigned here (1-based); ``summarize_update`` leaves placeholder 0.
- Avoid merging stream+invoke into one pass unless LangGraph API guarantees
  identical final state — tests rely on current two-phase pattern.
- 기본 dry_run·비영속은 로컬 안전 설정.
- ``step_index``는 여기서 1부터 부여.
- stream+invoke 통합은 최종 state 동일성 검증 후에만.
"""

from __future__ import annotations

from deconstructor.graph.builder import build_graph
from deconstructor.pipeline.state_factory import make_initial_state
from deconstructor.pipeline.trace.summarize import summarize_update
from deconstructor.pipeline.trace.types import StepRecord, TracedRun


def run_pipeline_traced(
    raw_text: str,
    *,
    max_recursion_depth: int | None = None,
    dry_run: bool = True,
    persist_db: bool = False,
) -> TracedRun:
    """Run pipeline and capture each node visit (default: no DB).
    파이프라인 실행 + 노드 방문 기록 (기본: DB 없음)."""
    graph = build_graph(dry_run=dry_run, persist_db=persist_db)
    initial = make_initial_state(raw_text, max_recursion_depth=max_recursion_depth)

    steps: list[StepRecord] = []

    # Each stream event: {node_name: partial_state_update}.
    # stream 이벤트: {노드명: partial state update}.
    for idx, event in enumerate(graph.stream(initial, stream_mode="updates")):
        for node_name, update in event.items():
            record = summarize_update(node_name, update)
            record.step_index = idx + 1  # 1-based for human report
            steps.append(record)

    # Authoritative terminal state for report/json/weaver checks.
    # 리포트·JSON·weaver 검증용 최종 state.
    final_state = graph.invoke(initial)

    return TracedRun(final_state=final_state, steps=steps)
