"""
Link UI — LangGraph 파이프라인 (노드별·하위 단계 추적)
"""

from __future__ import annotations

from typing import Any

from deconstructor.graph.builder import build_graph
from deconstructor.pipeline.state_factory import make_initial_state
from deconstructor.pipeline.trace.summarize.compose import summarize_update
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.progress_ctx import bind_progress, set_node_step, unbind_progress

NODE_LABELS: dict[str, str] = {
    "deconstruct": "Gemini 사실 분해 (Deconstruct)",
    "verify": "재귀·깊이 검증 (Verify)",
    "dreamer": "가설 생성 (Dreamer Flash→Pro)",
    "fact_checker": "웹 팩트체크 (Tavily)",
    "skeptic": "인과 검증 (Skeptic)",
    "weaver": "그래프 엣지·Neo4j (Weaver)",
}


def _merge_pipeline_update(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, val in update.items():
        if key == "completed_facts" and val:
            prev = list(merged.get("completed_facts") or [])
            merged["completed_facts"] = prev + list(val)
        else:
            merged[key] = val
    return merged


def _detail_from_result(node_name: str, result: dict[str, Any] | None) -> str:
    if not result:
        return ""
    record = summarize_update(node_name, result)
    parts = [record.detail]
    if record.extracted_count is not None:
        parts.append(f"extracted={record.extracted_count}")
    if record.completed_count is not None:
        parts.append(f"completed={record.completed_count}")
    if record.verified_edge_count is not None:
        parts.append(f"verified={record.verified_edge_count}")
    if record.recursion_depth is not None:
        parts.append(f"depth={record.recursion_depth}")
    return "; ".join(p for p in parts if p)[:160]


def run_pipeline_with_steps(
    tracker: LinkStepTracker,
    batch_idx: int,
    raw_text: str,
    *,
    dry_run: bool = False,
    dreamer_dry_run: bool | None = None,
    fact_checker_dry_run: bool | None = None,
    persist_db: bool = False,
    enable_dreamer: bool = True,
    max_recursion_depth: int | None = None,
    analysis_run_id: str | None = None,
) -> dict[str, Any]:
    """파이프라인 1회 실행 — LangGraph task 시작/완료 + 노드 내부 하위 단계."""
    prefix = f"S4-{batch_idx}"
    chars = len(raw_text)

    tracker.start(f"{prefix}-COMPILE", "LangGraph 컴파일", f"dreamer={enable_dreamer}")
    graph = build_graph(
        dry_run=dry_run,
        dreamer_dry_run=dreamer_dry_run,
        fact_checker_dry_run=fact_checker_dry_run,
        persist_db=persist_db,
        enable_dreamer=enable_dreamer,
    )
    tracker.ok(f"{prefix}-COMPILE")

    tracker.start(f"{prefix}-INIT", "초기 state 생성", f"{chars}자")
    initial = make_initial_state(
        raw_text,
        max_recursion_depth=max_recursion_depth,
        enable_dreamer=enable_dreamer,
        analysis_run_id=analysis_run_id,
    )
    tracker.ok(f"{prefix}-INIT")

    visit_count: dict[str, int] = {}
    open_steps: dict[str, str] = {}
    final_state = dict(initial)

    bind_progress(tracker)
    try:
        for event in graph.stream(initial, stream_mode="debug"):
            ev_type = event.get("type")
            if ev_type not in ("task", "task_result"):
                continue
            payload = event.get("payload") or {}
            node_name = payload.get("name")
            if node_name not in NODE_LABELS:
                continue
            task_id = str(payload.get("id") or "")

            if ev_type == "task":
                visit_count[node_name] = visit_count.get(node_name, 0) + 1
                visit = visit_count[node_name]
                step = f"{prefix}-NODE-{node_name}"
                if visit > 1:
                    step = f"{step}-R{visit}"
                open_steps[task_id] = step
                label = NODE_LABELS[node_name]
                set_node_step(step)
                tracker.start(step, label, f"방문 {visit}")
                continue

            step = open_steps.pop(task_id, None)
            if not step:
                continue
            result = payload.get("result")
            if isinstance(result, dict):
                final_state = _merge_pipeline_update(final_state, result)
            detail = _detail_from_result(node_name, result if isinstance(result, dict) else None)
            tracker.ok(step, detail or "완료")
            set_node_step("")
    finally:
        unbind_progress()

    tracker.start(f"{prefix}-DONE", "파이프라인 완료")
    facts = len(final_state.get("completed_facts") or [])
    edges = len(final_state.get("verified_edges") or [])
    tracker.ok(f"{prefix}-DONE", f"facts={facts} edges={edges}")
    return final_state
