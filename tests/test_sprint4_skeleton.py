"""
Sprint 4 — skeleton index + UI wiring (SP4-TEST-01).

See ``docs/design/SPRINT-4-skeleton-ui-spec.md``.
"""

from __future__ import annotations

from deconstructor.skeleton import skeleton_index
from deconstructor.skeleton.rules import (
    find_gaps,
    find_strong_chains,
    is_conclusion_like,
)
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode


def _node(nid: str, subject: str, state_change: str = "changed", **kw) -> GraphNode:
    return GraphNode(
        id=nid,
        subject=subject,
        state_change=state_change,
        timestamp=None,
        trigger_event="t",
        **kw,
    )


def _edge(src: str, tgt: str, kind: str = "CAUSES") -> GraphEdge:
    return GraphEdge(
        source_id=src,
        target_id=tgt,
        probability=0.9,
        latency=None,
        edge_kind=kind,
    )


def test_sp4_idx02_gap_leaf_without_cause():
    nodes = [_node("c", "Yield", "increased sharply")]
    gaps = find_gaps(nodes, [])
    assert len(gaps) == 1
    assert gaps[0]["id"] == "c"
    assert gaps[0]["reason"] in ("outcome_without_cause", "orphan_conclusion")


def test_sp4_idx02_gap_unsupported_root_cause():
    nodes = [
        _node("a", "Heat", "rose"),
        _node("b", "Pressure", "increased"),
    ]
    edges = [_edge("a", "b")]
    gaps = find_gaps(nodes, edges)
    gap_ids = {g["id"] for g in gaps}
    assert "a" in gap_ids


def test_sp4_idx03_strong_chain_two_edges():
    nodes = [
        _node("a", "Ni catalyst", "active"),
        _node("b", "Reaction rate", "rose"),
        _node("c", "Yield", "increased"),
    ]
    edges = [_edge("a", "b"), _edge("b", "c")]
    chains = find_strong_chains(nodes, edges)
    assert len(chains) >= 1
    assert chains[0]["length"] >= 2
    assert chains[0]["node_ids"] == ["a", "b", "c"]


def test_sp4_idx05_bridge_excluded_from_strong():
    nodes = [
        _node("a", "Topic A", "x"),
        _node("b", "Topic B", "y"),
    ]
    edges = [_edge("a", "b", kind="BRIDGE")]
    chains = find_strong_chains(nodes, edges)
    assert chains == []


def test_sp4_idx01_empty_graph():
    sk = skeleton_index([], [])
    assert sk["gap_count"] == 0
    assert sk["strong_chain_count"] == 0
    assert sk["weak_count"] == 0
    assert sk["outline"] == []


def test_sp4_out01_outline_roles():
    nodes = [
        _node("a", "Cause", "initiated"),
        _node("b", "Effect", "increased"),
    ]
    edges = [_edge("a", "b")]
    sk = skeleton_index(nodes, edges)
    roles = {o["id"]: o["role"] for o in sk["outline"]}
    assert roles["a"] in ("strong", "other", "gap")
    assert roles["b"] in ("strong", "gap", "other")
    assert all(o["role"] in ("gap", "strong", "weak", "other") for o in sk["outline"])


def test_sp4_api01_result_shape_keys():
    nodes = [_node("x", "Lonely", "result achieved")]
    sk = skeleton_index(nodes, [])
    for key in (
        "gap_count",
        "strong_chain_count",
        "weak_count",
        "gaps",
        "strong_chains",
        "weak",
        "outline",
        "health_summary",
    ):
        assert key in sk
    assert sk["health_summary"]["node_count"] == 1


def test_sp4_idx02_conclusion_like_heuristic():
    leaf = _node("l", "Output", "stable")
    assert is_conclusion_like(leaf, 0, 0) is True
    mid = _node("m", "Factor", "rose")
    assert is_conclusion_like(mid, 1, 1) is True
