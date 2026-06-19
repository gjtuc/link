"""
Step 2 — Dreamer stub / node 단위 테스트
========================================
"""

from datetime import datetime

import pytest

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.dreamer.stub import stub_dream_hypotheses
from deconstructor.models import AtomicFact
from deconstructor.pipeline.state_factory import make_initial_state


def _factory_blackout_source() -> AtomicFact:
    return AtomicFact(
        id="src-factory-a",
        subject="factory A grid power",
        state_change="supply -> interrupted",
        timestamp=datetime(2026, 1, 1, 10, 0, 0),
        is_atomic=True,
        source_type="extracted",
        check_status="active",
    )


def test_stub_returns_three_hypotheses_for_factory_headline():
    source = _factory_blackout_source()
    result = stub_dream_hypotheses(
        [source],
        raw_text="[단독] A공장 정전 발생",
    )
    assert len(result.hypotheses) == 3
    assert all(h.source_fact_id == source.id for h in result.hypotheses)


def test_apply_forces_inferred_pending():
    source = _factory_blackout_source()
    stub_list = stub_dream_hypotheses([source], raw_text="A공장 정전")
    inferred = apply_hypotheses(stub_list, [source])
    assert len(inferred) == 3
    for fact in inferred:
        assert fact.source_type == "inferred"
        assert fact.check_status == "pending"
        assert fact.is_atomic is True


def test_dreamer_node_stub_populates_inferred_facts(capsys):
    state = make_initial_state("A공장 정전")
    state["completed_facts"] = [_factory_blackout_source()]

    out = dreamer_node(state, dry_run=True)

    assert len(out["inferred_facts"]) == 3
    assert out["inferred_facts"][0].source_type == "inferred"
    assert out["inferred_facts"][0].check_status == "pending"
    assert len(out["dreamer_log"]) >= 2

    captured = capsys.readouterr().out
    assert "[DREAM-S2-4]" in captured
    assert "[DREAM-S2-5]" in captured
    assert "[DREAM-S2-6]" in captured


def test_dreamer_node_skips_without_sources():
    state = make_initial_state("empty")
    out = dreamer_node(state, dry_run=True)
    assert out["inferred_facts"] == []
    assert "skip" in out["dreamer_log"][0].lower()


def test_stub_requires_source_facts():
    with pytest.raises(ValueError):
        stub_dream_hypotheses([])
