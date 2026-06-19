"""
그래프 HTML 갱신 — Neo4j fetch → pyvis (공통)
=============================================

``pipeline_batch`` 의 S7 렌더 단계와 동일 로직을
사용자 가설 MVP·향후 증분 검증 API 에서 재사용한다.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPH_HTML = ROOT / "graph_output.html"


def refresh_graph_from_neo4j(
    *,
    title: str = "Deconstructor Causal Graph",
    trigger_events: list[str] | None = None,
    analysis_run_id: str | None = None,
) -> bool:
    """
    Neo4j ``fetch_causal_graph`` → ``graph_output.html`` 재생성.

    ``analysis_run_id`` / ``trigger_events`` 가 없으면 ``graph_context`` 최신 값 사용.
    """
    from deconstructor.viz.neo4j_utils import fetch_causal_graph, neo4j_is_available
    from deconstructor.viz.visualizer import build_pyvis_network, inject_legend_into_html
    from deconstructor.web.graph_context import (
        get_last_analysis_run_id,
        get_last_trigger_events,
    )

    if not neo4j_is_available():
        return False

    run_id = analysis_run_id if analysis_run_id is not None else get_last_analysis_run_id()
    events = trigger_events if trigger_events is not None else get_last_trigger_events()
    result = fetch_causal_graph(
        analysis_run_id=run_id,
        trigger_events=events,
    )
    if not result.nodes:
        return False

    net = build_pyvis_network(result.nodes, result.edges, title=title)
    output_path = GRAPH_HTML.resolve()
    net.save_graph(str(output_path))
    inject_legend_into_html(output_path)
    return True
