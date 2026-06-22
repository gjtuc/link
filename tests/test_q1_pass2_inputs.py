"""μ-Q1-02 — pass2 Dreamer source selection (offline)."""

from __future__ import annotations

from datetime import datetime

from deconstructor.agents.dreamer.pass2_inputs import select_pass2_source_facts
from deconstructor.models import AtomicFact, CausalEdge


def _fact(fid: str, subject: str, state_change: str = "changed", **kw) -> AtomicFact:
    return AtomicFact(
        id=fid,
        subject=subject,
        state_change=state_change,
        timestamp=datetime(2026, 1, 1),
        is_atomic=True,
        source_type=kw.get("source_type", "extracted"),
        check_status=kw.get("check_status", "active"),
    )


def _edge(src: str, tgt: str) -> CausalEdge:
    return CausalEdge(source_fact_id=src, target_fact_id=tgt, probability=0.9)


def _ids(facts: list[AtomicFact]) -> set[str]:
    return {f.id for f in facts}


def test_chain_endpoints_include_a_and_c_exclude_interior_b():
    facts = [
        _fact("a", "Heat", "rose"),
        _fact("b", "Pressure", "increased"),
        _fact("c", "Yield", "increased sharply"),
    ]
    edges = [_edge("a", "b"), _edge("b", "c")]
    selected = select_pass2_source_facts(facts, edges, gap_nodes=[])
    assert _ids(selected) == {"a", "c"}


def test_single_edge_both_endpoints_included():
    facts = [_fact("a", "Ni catalyst", "active"), _fact("b", "Rate", "rose")]
    edges = [_edge("a", "b")]
    selected = select_pass2_source_facts(facts, edges, gap_nodes=[])
    assert _ids(selected) == {"a", "b"}


def test_gap_node_included_without_edges():
    facts = [_fact("g", "Yield", "increased sharply")]
    gaps = [{"id": "g", "subject": "Yield", "state_change": "increased sharply", "reason": "outcome_without_cause"}]
    selected = select_pass2_source_facts(facts, [], gap_nodes=gaps)
    assert _ids(selected) == {"g"}


def test_orphan_extracted_excluded():
    facts = [
        _fact("a", "Heat", "rose"),
        _fact("b", "Pressure", "increased"),
        _fact("o", "Orphan memo", "noted", source_type="extracted"),
    ]
    edges = [_edge("a", "b")]
    selected = select_pass2_source_facts(facts, edges, gap_nodes=[])
    assert "o" not in _ids(selected)


def test_gap_plus_endpoint_union():
    facts = [
        _fact("a", "Heat", "rose"),
        _fact("b", "Pressure", "increased"),
        _fact("g", "Yield", "increased sharply"),
    ]
    edges = [_edge("a", "b")]
    gaps = [{"id": "g", "subject": "Yield", "state_change": "increased sharply", "reason": "outcome_without_cause"}]
    selected = select_pass2_source_facts(facts, edges, gap_nodes=gaps)
    assert _ids(selected) == {"a", "b", "g"}


def test_inferred_facts_never_selected_even_if_in_gap_list():
    facts = [
        _fact("a", "Heat", "rose"),
        _fact("inf", "Guess", "maybe", source_type="inferred", check_status="pending"),
    ]
    gaps = [{"id": "inf", "subject": "Guess", "state_change": "maybe", "reason": "x"}]
    selected = select_pass2_source_facts(facts, [], gap_nodes=gaps)
    assert _ids(selected) == set()


def test_interior_excluded_gap_at_root_included():
    """A→B→C with G as separate gap leaf — B interior out, G in."""
    facts = [
        _fact("a", "Cause", "started"),
        _fact("b", "Middle", "propagated"),
        _fact("c", "Effect", "finished"),
        _fact("g", "Outcome", "increased sharply"),
    ]
    edges = [_edge("a", "b"), _edge("b", "c")]
    gaps = [{"id": "g", "subject": "Outcome", "state_change": "increased sharply", "reason": "orphan_conclusion"}]
    selected = select_pass2_source_facts(facts, edges, gap_nodes=gaps)
    assert _ids(selected) == {"a", "c", "g"}
