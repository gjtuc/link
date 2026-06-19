"""Step 3 — Watcher trigger (Neo4j + Console + WeaverResult)."""

from unittest.mock import MagicMock

from deconstructor.agents.watcher.memory import build_memory_storm_state
from deconstructor.agents.watcher.run import run_watcher_in_memory, run_watcher_neo4j
from deconstructor.agents.watcher.schemas import StormCandidate
from deconstructor.agents.watcher.trigger import (
    ANSI_RED,
    emit_storm_trigger,
    trigger_storm_candidates_neo4j,
)
from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.weaver.node import weaver_node


def test_emit_storm_trigger_prints_red_ansi(capsys):
    emit_storm_trigger("A공장")
    captured = capsys.readouterr().out
    assert "[STORM-S3-TRIGGER] Perfect Storm Detected on node: A공장" in captured
    assert ANSI_RED in captured


def test_run_watcher_in_memory_triggers_and_returns_subjects(capsys):
    grid = AtomicFact(
        id="g1",
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        source_type="extracted",
    )
    supply = AtomicFact(
        id="s1",
        subject="supply",
        state_change="voltage -> collapsed",
        is_atomic=True,
        source_type="verified",
        check_status="promoted",
    )
    factory = AtomicFact(
        id="f1",
        subject="A공장",
        state_change="output -> halted",
        is_atomic=True,
    )
    edges = [
        CausalEdge(
            source_fact_id=grid.id,
            target_fact_id=factory.id,
            probability=0.9,
            latency=1000,
        ),
        CausalEdge(
            source_fact_id=supply.id,
            target_fact_id=factory.id,
            probability=0.85,
            latency=2000,
        ),
    ]

    subjects = run_watcher_in_memory([grid, supply, factory], edges)
    captured = capsys.readouterr().out

    assert subjects == ["A공장"]
    assert "[STORM-S3-TRIGGER]" in captured
    assert ANSI_RED in captured
    assert "A공장" in captured


def test_trigger_storm_candidates_neo4j_mock(capsys):
    session = MagicMock()
    session.run.return_value.single.return_value = {"subject": "A공장"}
    candidates = [
        StormCandidate(
            fact_id="f1",
            subject="A공장",
            stress_level=70,
            incoming_count=2,
        )
    ]

    subjects = trigger_storm_candidates_neo4j(session, candidates)
    captured = capsys.readouterr().out

    assert subjects == ["A공장"]
    assert "[STORM-S3-TRIGGER]" in captured
    assert ANSI_RED in captured
    session.run.assert_called_once()


def test_run_watcher_neo4j_end_to_end_mock(capsys):
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session

    scan_result = MagicMock()
    scan_result.data.return_value = [
        {
            "id": "f1",
            "subject": "A공장",
            "stress_level": 110,
            "incoming_count": 1,
        }
    ]
    trigger_result = MagicMock()
    trigger_result.single.return_value = {"subject": "A공장"}

    def run_side_effect(query, **kwargs):
        if "SET t.is_critical" in query:
            return trigger_result
        return scan_result

    session.run.side_effect = run_side_effect

    subjects = run_watcher_neo4j(driver)
    captured = capsys.readouterr().out

    assert subjects == ["A공장"]
    assert "[STORM-S3-TRIGGER]" in captured
    assert ANSI_RED in captured


def test_weaver_node_console_attaches_critical_subjects(capsys):
    grid = AtomicFact(
        id="g1",
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        source_type="extracted",
    )
    supply = AtomicFact(
        id="s1",
        subject="supply",
        state_change="voltage -> collapsed",
        is_atomic=True,
        source_type="verified",
        check_status="promoted",
    )
    factory = AtomicFact(
        id="f1",
        subject="A공장",
        state_change="output -> halted",
        is_atomic=True,
    )
    state = {
        "raw_text": "headline",
        "verified_edges": [
            CausalEdge(
                source_fact_id=grid.id,
                target_fact_id=factory.id,
                probability=0.9,
                latency=1000,
            ),
            CausalEdge(
                source_fact_id=supply.id,
                target_fact_id=factory.id,
                probability=0.85,
                latency=2000,
            ),
        ],
        "completed_facts": [grid, factory],
        "promoted_facts": [supply],
        "partial_run": False,
    }

    out = weaver_node(state, persist_db=False)  # type: ignore[arg-type]
    captured = capsys.readouterr().out

    assert out["weaver_result"].critical_subjects == ["A공장"]
    assert "[STORM-S3-TRIGGER]" in captured
    assert ANSI_RED in captured
