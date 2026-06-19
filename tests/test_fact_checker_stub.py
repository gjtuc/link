"""Step 3 — Fact-Checker stub + Dreamer 연동 테스트."""

from datetime import datetime

import pytest

from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.fact_checker.node import fact_checker_node
from deconstructor.agents.fact_checker.search.factory import require_tavily_api_key
from deconstructor.agents.fact_checker.query_builder import build_search_query
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


def test_query_builder_includes_subject_and_date():
    fact = _factory_blackout_source()
    q = build_search_query(fact)
    assert "factory" in q.lower()
    assert "2026" in q


def test_require_tavily_api_key_raises_when_missing(monkeypatch):
    monkeypatch.setattr(
        "deconstructor.agents.fact_checker.search.factory.config.TAVILY_API_KEY",
        "",
    )
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        require_tavily_api_key()


def test_fact_checker_stub_promote_two_drop_one(capsys):
    state = make_initial_state("A공장 정전")
    state["completed_facts"] = [_factory_blackout_source()]

    dream_out = dreamer_node(state, dry_run=True)
    state["inferred_facts"] = dream_out["inferred_facts"]
    assert len(state["inferred_facts"]) == 3

    check_out = fact_checker_node(state, dry_run=True)

    promoted = check_out["promoted_facts"]
    dropped = check_out["dropped_hypotheses"]

    assert len(promoted) == 2
    assert len(dropped) == 1

    for p in promoted:
        assert p.source_type == "inferred"
        assert p.check_status == "promoted"

    ghost = dropped[0].ghost_fact
    assert ghost.source_type == "inferred"
    assert ghost.check_status == "dropped"
    assert "equity" in dropped[0].subject.lower() or "price" in dropped[0].state_change.lower()

    captured = capsys.readouterr().out
    assert "[CHECK-S3-PROMOTE]" in captured or "[CHECK-S3-apply]" in captured
    assert "[CHECK-S3-DROP]" in captured
    assert "[CHECK-S3-node]" in captured


def test_dreamer_then_checker_e2e_stub_pipeline():
    """Dreamer 3가설 → Fact-Checker: 2 green-ready + 1 ghost-ready."""
    state = make_initial_state("[단독] A공장 정전")
    state["completed_facts"] = [_factory_blackout_source()]

    state.update(dreamer_node(state, dry_run=True))
    state.update(fact_checker_node(state, dry_run=True))

    assert len(state["promoted_facts"]) == 2
    assert len(state["dropped_hypotheses"]) == 1
    assert state["dropped_hypotheses"][0].ghost_fact.check_status == "dropped"
