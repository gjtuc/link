"""
Link UI — 배치 분석 오케스트레이션 (세분화 단계 추적)
"""

from __future__ import annotations

import uuid
from pathlib import Path

from deconstructor.web.extract import ExtractedSource
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.graph_context import set_last_graph_filter
from deconstructor.web.pipeline_link import run_pipeline_with_steps

ROOT = Path(__file__).resolve().parents[2]
GRAPH_HTML = ROOT / "graph_output.html"


def run_pipeline_batch(
    sources: list[ExtractedSource],
    tracker: LinkStepTracker | None = None,
) -> dict:
    """추출된 소스 → 파이프라인 → Neo4j → 그래프 HTML. 실패 시 ``failed_step``·``steps`` 포함."""
    tr = tracker or LinkStepTracker()
    try:
        return _run_pipeline_batch_inner(sources, tr)
    except Exception as exc:
        return tr.fail(exc)


def _ensure_neo4j_tracked(tracker: LinkStepTracker, pipeline_states: list) -> tuple[bool, dict | None]:
    from deconstructor.neo4j_launcher import (
        ensure_neo4j_running,
        persist_state_to_neo4j,
        probe_neo4j_installation,
    )
    from deconstructor.viz.neo4j_utils import neo4j_is_available

    if neo4j_is_available():
        tracker.skip("S5-NEO4J-ENSURE", "이미 bolt 연결됨")
        return True, None

    tracker.start("S5-NEO4J-PROBE", "Neo4j 설치 경로 탐색")
    probe = probe_neo4j_installation(ROOT)
    if not probe.any_installed:
        tracker.skip("S5-NEO4J-PROBE", "미설치")
        return False, {
            "attempted": False,
            "available": False,
            "method": "none",
            "message": "Neo4j/Docker 미설치",
        }
    parts = []
    if probe.docker_cli:
        parts.append("docker")
    if probe.desktop_exe:
        parts.append("desktop")
    tracker.ok("S5-NEO4J-PROBE", ", ".join(parts) or "found")

    tracker.start("S5-NEO4J-START", "Neo4j 기동·bolt 대기", "최대 90초")
    ensure = ensure_neo4j_running(ROOT, wait_timeout_sec=90)
    neo4j_sync = {
        "attempted": True,
        "available": ensure.available,
        "method": ensure.method,
        "message": ensure.message,
        "waited_sec": round(ensure.waited_sec, 1),
    }
    if ensure.available:
        tracker.ok("S5-NEO4J-START", f"{ensure.method} ({ensure.waited_sec:.0f}s)")
        for i, state in enumerate(pipeline_states, start=1):
            bf = f"S5-NEO4J-BACKFILL-{i}"
            tracker.start(bf, f"Neo4j 백필 {i}/{len(pipeline_states)}", "weaver persist")
            persist_state_to_neo4j(state)
            tracker.ok(bf)
        return True, neo4j_sync

    tracker.skip("S5-NEO4J-START", "기동 실패", ensure.message[:120])
    return False, neo4j_sync


def _render_graph_tracked(tracker: LinkStepTracker, nodes, edges) -> None:
    from deconstructor.viz.visualizer import build_pyvis_network, inject_legend_into_html

    tracker.start("S7-RENDER-NET", "pyvis 네트워크 생성", f"nodes={len(nodes)}")
    net = build_pyvis_network(nodes, edges, title="Deconstructor Causal Graph")
    tracker.ok("S7-RENDER-NET")

    tracker.start("S7-RENDER-SAVE", "HTML 파일 저장", GRAPH_HTML.name)
    output_path = GRAPH_HTML.resolve()
    net.save_graph(str(output_path))
    tracker.ok("S7-RENDER-SAVE")

    tracker.start("S7-RENDER-LEGEND", "범례·hover JS 주입")
    inject_legend_into_html(output_path)
    tracker.ok("S7-RENDER-LEGEND")


def _run_pipeline_batch_inner(sources: list[ExtractedSource], tracker: LinkStepTracker) -> dict:
    from deconstructor import config
    from deconstructor.report import format_dry_run_report
    from deconstructor.viz.neo4j_utils import fetch_causal_graph, neo4j_is_available
    from deconstructor.viz.state_graph import graph_from_pipeline_state, merge_graph_results

    tracker.start("S1-INPUT", "입력 검증", f"{len(sources)}건")
    if not sources:
        raise ValueError("분석할 소스가 없습니다")
    tracker.ok("S1-INPUT")

    batch_run_id = str(uuid.uuid4())
    batch_trigger_events = [src.text for src in sources]
    set_last_graph_filter(
        analysis_run_id=batch_run_id,
        trigger_events=batch_trigger_events,
    )

    tracker.start("S3-NEO4J-BOLT", "Neo4j bolt 핑")
    use_db = neo4j_is_available()
    tracker.ok("S3-NEO4J-BOLT", "연결됨" if use_db else "오프라인")

    has_tavily = bool(config.TAVILY_API_KEY)
    tracker.start("S3-CONFIG-TAVILY", "Fact-Checker", "live" if has_tavily else "stub")
    tracker.ok("S3-CONFIG-TAVILY")

    tracker.start("S3-CONFIG-GEMINI", "LLM (Deconstruct·Dreamer)")
    tracker.ok("S3-CONFIG-GEMINI", "Gemini API")

    neo4j_sync: dict | None = None
    runs: list[dict] = []
    session_graphs: list = []
    pipeline_states: list = []

    for idx, src in enumerate(sources, start=1):
        tracker.start(
            f"S4-{idx}-PREP",
            f"소스 {idx}/{len(sources)} 준비",
            f"{src.kind}: {src.label[:50]}",
        )
        tracker.ok(f"S4-{idx}-PREP", f"{len(src.text)}자")

        try:
            state = run_pipeline_with_steps(
                tracker,
                idx,
                src.text,
                persist_db=use_db,
                enable_dreamer=True,
                fact_checker_dry_run=not has_tavily,
                analysis_run_id=batch_run_id,
            )
        except Exception as exc:
            raise RuntimeError(f"파이프라인 실패 ({src.label}): {exc}") from exc

        pipeline_states.append(state)

        tracker.start(f"S4-{idx}-REPORT", "리포트 요약")
        report = format_dry_run_report(state)
        tracker.ok(f"S4-{idx}-REPORT")

        verified = state.get("verified_edges") or []
        completed = state.get("completed_facts") or []
        promoted = state.get("promoted_facts") or []
        dropped = state.get("dropped_hypotheses") or []

        if not use_db:
            tracker.start(f"S4-{idx}-SESSION-GRAPH", "세션 그래프 변환")
            session_graphs.append(graph_from_pipeline_state(state))
            tracker.ok(f"S4-{idx}-SESSION-GRAPH")

        runs.append(
            {
                "index": idx,
                "kind": src.kind,
                "label": src.label,
                "chars": len(src.text),
                "verified_edges": len(verified),
                "atomic_facts": len(completed),
                "dreamer_promoted": len(promoted),
                "dreamer_dropped": len(dropped),
                "preview": src.text[:240] + ("…" if len(src.text) > 240 else ""),
                "report_excerpt": "\n".join(report.splitlines()[:12]),
            }
        )

    if not use_db:
        use_db, neo4j_sync = _ensure_neo4j_tracked(tracker, pipeline_states)

    tracker.start("S6-GRAPH-LOAD", "그래프 데이터 로드")
    if use_db:
        tracker.ok("S6-GRAPH-LOAD", "Neo4j Cypher")
        tracker.start("S6-GRAPH-QUERY", "인과 그래프 조회", "현재 배치만")
        fetched = fetch_causal_graph(
            max_nodes=300,
            analysis_run_id=batch_run_id,
            trigger_events=batch_trigger_events,
        )
        tracker.ok(
            "S6-GRAPH-QUERY",
            f"nodes={len(fetched.nodes)} matched={fetched.matched_nodes_in_db}",
        )
    else:
        tracker.ok("S6-GRAPH-LOAD", "세션 병합")
        tracker.start("S6-GRAPH-MERGE", "세션 그래프 병합")
        fetched = merge_graph_results(session_graphs)
        tracker.ok("S6-GRAPH-MERGE", f"nodes={len(fetched.nodes)}")

    _render_graph_tracked(tracker, fetched.nodes, fetched.edges)

    from deconstructor.web.debug_report import build_pipeline_debug

    pipeline_debug = build_pipeline_debug(
        pipeline_states,
        fetched=fetched,
        batch_run_id=batch_run_id,
        fact_checker_mode="stub" if not has_tavily else "live",
    )

    return {
        "ok": True,
        "steps": tracker.to_list(),
        "neo4j": use_db,
        "neo4j_sync": neo4j_sync,
        "neo4j_persisted": use_db,
        "items_processed": len(sources),
        "sources": runs,
        "nodes": len(fetched.nodes),
        "edges": len(fetched.edges),
        "graph_filter": {
            "analysis_run_id": batch_run_id,
            "trigger_events": batch_trigger_events,
            "matched_nodes_in_db": fetched.matched_nodes_in_db,
            "total_nodes_in_db": fetched.total_nodes_in_db,
        },
        "verified_edges_total": sum(r["verified_edges"] for r in runs),
        "atomic_facts_total": sum(r["atomic_facts"] for r in runs),
        "pipeline_debug": pipeline_debug,
    }
