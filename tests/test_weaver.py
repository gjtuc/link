"""Tests for Weaver console/neo4j modes (Phase 10)."""

from deconstructor.models import CausalEdge
from deconstructor.weaver.console_store import ConsoleWeaver
from deconstructor.weaver.resolve import facts_for_verified_edges
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT


def test_resolve_only_edge_endpoints():
    edges = [
        CausalEdge(
            source_fact_id=GRID_OFF.id,
            target_fact_id=MOTOR_STOP.id,
            probability=0.9,
            latency=1000,
        )
    ]
    facts = facts_for_verified_edges(
        [GRID_OFF, MOTOR_STOP, WEATHER_HOT], edges
    )
    ids = {f.id for f in facts}
    assert ids == {GRID_OFF.id, MOTOR_STOP.id}
    assert WEATHER_HOT.id not in ids


def test_resolve_empty_when_no_edges():
    assert facts_for_verified_edges([GRID_OFF, MOTOR_STOP], []) == []


def test_console_weaver_no_db():
    edges = [
        CausalEdge(
            source_fact_id=GRID_OFF.id,
            target_fact_id=MOTOR_STOP.id,
            probability=0.9,
            latency=1000,
        )
    ]
    facts = facts_for_verified_edges([GRID_OFF, MOTOR_STOP], edges)
    result = ConsoleWeaver().persist(
        trigger_event="test",
        facts=facts,
        edges=edges,
        partial_run=False,
    )
    assert result.mode == "console"
    assert result.nodes_written == 2
    assert result.edges_written == 1


def test_console_weaver_skips_empty_edges():
    result = ConsoleWeaver().persist(
        trigger_event="test",
        facts=[],
        edges=[],
        partial_run=True,
    )
    assert result.nodes_written == 0
    assert result.skipped_reason != ""
    assert result.partial_run is True
