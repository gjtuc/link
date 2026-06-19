"""Step 2 — Watcher scan (Neo4j + in-memory)."""

from unittest.mock import MagicMock

from deconstructor.agents.watcher.criteria import is_storm_candidate
from deconstructor.agents.watcher.memory import build_memory_storm_state
from deconstructor.agents.watcher.scan import STORM_CANDIDATES_CYPHER, find_storm_candidates
from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.storm.types import STRESS_THRESHOLD


def test_is_storm_candidate_triggers_on_two_incoming_edges():
    assert is_storm_candidate(stress_level=10, incoming_count=2, is_critical=False) is True


def test_is_storm_candidate_triggers_on_stress_above_threshold():
    assert is_storm_candidate(
        stress_level=STRESS_THRESHOLD + 1,
        incoming_count=1,
        is_critical=False,
    ) is True


def test_is_storm_candidate_skips_already_critical():
    assert is_storm_candidate(stress_level=200, incoming_count=5, is_critical=True) is False


def test_is_storm_candidate_rejects_at_threshold_not_above():
    assert is_storm_candidate(
        stress_level=STRESS_THRESHOLD,
        incoming_count=1,
        is_critical=False,
    ) is False


def test_find_storm_candidates_neo4j_mock():
    session = MagicMock()
    session.run.return_value.data.return_value = [
        {
            "id": "tgt-1",
            "subject": "A공장",
            "stress_level": 70,
            "incoming_count": 2,
        }
    ]

    candidates = find_storm_candidates(session)

    assert len(candidates) == 1
    assert candidates[0].subject == "A공장"
    assert candidates[0].incoming_count == 2
    session.run.assert_called_once()
    assert STORM_CANDIDATES_CYPHER.strip() in session.run.call_args.args[0].strip()


def test_memory_scan_detects_perfect_storm_on_two_causes():
    grid = AtomicFact(
        id="src-grid",
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        source_type="extracted",
    )
    supply = AtomicFact(
        id="src-supply",
        subject="supply",
        state_change="voltage -> collapsed",
        is_atomic=True,
        source_type="verified",
        check_status="promoted",
    )
    factory = AtomicFact(
        id="tgt-factory",
        subject="A공장",
        state_change="output -> halted",
        is_atomic=True,
        source_type="extracted",
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

    state = build_memory_storm_state([grid, supply, factory], edges)
    candidates = state.find_candidates()

    assert len(candidates) == 1
    assert candidates[0].subject == "A공장"
    assert candidates[0].incoming_count == 2
    assert candidates[0].stress_level == 70


def test_memory_scan_inferred_cause_counts_incoming_but_zero_stress():
    inferred = AtomicFact(
        id="src-inf",
        subject="rumor",
        state_change="speculation -> spread",
        is_atomic=True,
        source_type="inferred",
        check_status="pending",
    )
    extracted = AtomicFact(
        id="src-ext",
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        source_type="extracted",
    )
    target = AtomicFact(
        id="tgt",
        subject="factory",
        state_change="output -> halted",
        is_atomic=True,
    )
    edges = [
        CausalEdge(
            source_fact_id=inferred.id,
            target_fact_id=target.id,
            probability=0.3,
            latency=1000,
        ),
        CausalEdge(
            source_fact_id=extracted.id,
            target_fact_id=target.id,
            probability=0.9,
            latency=2000,
        ),
    ]

    state = build_memory_storm_state([inferred, extracted, target], edges)
    node = state.nodes[target.id]

    assert node.stress_level == 30
    assert node.incoming_count == 2
    assert len(state.find_candidates()) == 1
