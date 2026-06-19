"""Step 1 — Storm stress weights ([STORM-S1-2], [STORM-S1-3])."""

from unittest.mock import MagicMock

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.storm.stress import compute_stress_delta
from deconstructor.storm.types import (
    STRESS_THRESHOLD,
    STRESS_WEIGHT_EXTRACTED,
    STRESS_WEIGHT_INFERRED,
    STRESS_WEIGHT_VERIFIED,
)
from deconstructor.weaver.neo4j_store import Neo4jWeaver


def test_stress_weight_constants():
    assert STRESS_WEIGHT_VERIFIED == 40
    assert STRESS_WEIGHT_EXTRACTED == 30
    assert STRESS_WEIGHT_INFERRED == 0
    assert STRESS_THRESHOLD == 100


def test_compute_stress_delta_verified():
    assert compute_stress_delta("verified") == 40


def test_compute_stress_delta_extracted():
    assert compute_stress_delta("extracted") == 30


def test_compute_stress_delta_inferred_is_zero():
    assert compute_stress_delta("inferred") == 0


def test_neo4j_persist_merges_storm_fields_on_fact():
    session = MagicMock()
    driver = MagicMock()
    driver.session.return_value.__enter__.return_value = session

    weaver = Neo4jWeaver.__new__(Neo4jWeaver)
    weaver._driver = driver

    src = AtomicFact(
        id="src-1",
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        source_type="extracted",
    )
    tgt = AtomicFact(
        id="tgt-1",
        subject="factory",
        state_change="output -> halted",
        is_atomic=True,
        source_type="verified",
        check_status="promoted",
    )
    edge = CausalEdge(
        source_fact_id=src.id,
        target_fact_id=tgt.id,
        probability=0.9,
        latency=60000,
    )

    weaver.persist(
        trigger_event="headline",
        facts=[src, tgt],
        edges=[edge],
    )

    merge_calls = [c for c in session.run.call_args_list if "stress_level" in str(c)]
    assert merge_calls, "expected MERGE with stress_level/is_critical fields"

    edge_calls = [c for c in session.run.call_args_list if "stress_delta" in str(c)]
    assert edge_calls, "expected CAUSES MERGE to bump target stress_level"
    assert edge_calls[0].kwargs.get("stress_delta") == 30
