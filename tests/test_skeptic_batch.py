"""Tests for batch edge filter and rule registry."""

from deconstructor.models import CausalEdge
from deconstructor.skeptic.batch_filter import resolve_bidirectional_conflicts
from deconstructor.skeptic.rules.registry import build_rule_registry


def test_registry_has_eleven_rules():
    assert len(build_rule_registry()) == 11


def test_bidirectional_keeps_best():
    edges = [
        CausalEdge(source_fact_id="x", target_fact_id="y", probability=0.7, latency=1),
        CausalEdge(source_fact_id="y", target_fact_id="x", probability=0.9, latency=1),
    ]
    out = resolve_bidirectional_conflicts(edges)
    assert len(out) == 1
    assert out[0].source_fact_id == "y"
    assert out[0].probability == 0.9
