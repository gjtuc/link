"""Tests for verified_edges trace handler."""

from deconstructor.models import CausalEdge
from deconstructor.pipeline.trace.summarize.handlers.edges import (
    count_verified_edges,
    detail_verified_edges,
)


def test_detail_verified_edges():
    edges = [
        CausalEdge(source_fact_id="a", target_fact_id="b", probability=0.9),
    ]
    update = {"verified_edges": edges}
    assert detail_verified_edges(update) == "edges=1"
    assert count_verified_edges(update) == 1


def test_detail_edges_missing():
    assert detail_verified_edges({}) is None
    assert count_verified_edges({}) is None
