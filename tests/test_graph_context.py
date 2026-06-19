"""그래프 trigger_event / analysis_run_id 필터 — 단위 테스트."""

from __future__ import annotations

from deconstructor.web.graph_context import (
    get_graph_filter_snapshot,
    get_last_analysis_run_id,
    get_last_trigger_events,
    normalize_trigger_event,
    set_last_graph_filter,
    set_last_trigger_events,
)


def test_normalize_trigger_event_collapses_whitespace():
    assert normalize_trigger_event("  hello\n  world  ") == "hello world"


def test_set_last_graph_filter():
    set_last_graph_filter(
        analysis_run_id="run-abc-123",
        trigger_events=["a", "b", "a"],
    )
    assert get_last_analysis_run_id() == "run-abc-123"
    assert get_last_trigger_events() == ["a", "b"]
    snap = get_graph_filter_snapshot()
    assert snap["analysis_run_id"] == "run-abc-123"
    assert snap["trigger_events"] == ["a", "b"]


def test_set_last_trigger_events_dedupes():
    set_last_trigger_events(["a", "b", "a"])
    assert get_last_trigger_events() == ["a", "b"]
    set_last_trigger_events(None)
    assert get_last_trigger_events() is None


def test_fetch_result_has_filter_fields():
    from deconstructor.viz.neo4j_utils import GraphFetchResult

    r = GraphFetchResult(
        nodes=[],
        edges=[],
        node_limit=300,
        truncated=False,
        total_nodes_in_db=10,
        trigger_events_filter=("hello",),
        analysis_run_id_filter="run-1",
        matched_nodes_in_db=3,
    )
    assert r.trigger_events_filter == ("hello",)
    assert r.analysis_run_id_filter == "run-1"
    assert r.matched_nodes_in_db == 3
