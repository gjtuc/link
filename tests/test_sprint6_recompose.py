"""
Sprint 6 — Re-compose ε-2~4 (SP6-TEST-01).

See ``docs/design/SPRINT-6-recompose-spec.md``.
"""

from __future__ import annotations

from deconstructor.recompose import recompose_index
from deconstructor.recompose.narrative import build_verified_narrative
from deconstructor.recompose.outline import build_rewrite_outline
from deconstructor.recompose.report import build_health_report
from deconstructor.skeleton import skeleton_index
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode


def _node(nid: str, subject: str, state_change: str) -> GraphNode:
    return GraphNode(
        id=nid,
        subject=subject,
        state_change=state_change,
        timestamp=None,
        trigger_event="t",
    )


def _edge(a: str, b: str) -> GraphEdge:
    return GraphEdge(source_id=a, target_id=b, probability=0.9, latency=None)


def _chain_skeleton() -> tuple[list[GraphNode], list[GraphEdge], dict]:
    nodes = [
        _node("a", "Heat input", "increased"),
        _node("b", "Reaction rate", "rose"),
        _node("c", "Yield", "increased sharply"),
    ]
    edges = [_edge("a", "b"), _edge("b", "c")]
    sk = skeleton_index(nodes, edges)
    return nodes, edges, sk


def test_sp6_nar01_strong_chain_narrative():
    nodes, edges, sk = _chain_skeleton()
    text = build_verified_narrative(nodes, edges, sk)
    assert "Because" in text
    assert "Heat input" in text
    assert "Yield" in text


def test_sp6_nar03_empty_narrative_placeholder():
    nodes = [_node("x", "Lonely", "stable")]
    sk = skeleton_index(nodes, [])
    text = build_verified_narrative(nodes, [], sk)
    assert text.startswith("(No verified")


def test_sp6_rpt02_report_contains_gap_section():
    nodes = [_node("g", "Output", "increased")]
    sk = skeleton_index(nodes, [])
    md = build_health_report(sk, fact_checker={"mode": "corpus"})
    assert "Gap" in md
    assert "NG-3" in md
    assert "corpus" in md


def test_sp6_out01_gap_rewrite_hint():
    nodes = [_node("g", "Output", "increased")]
    sk = skeleton_index(nodes, [])
    outline = build_rewrite_outline(sk)
    assert any(item["kind"] == "fix_gap" for item in outline)
    assert any("upstream" in item["hint"].lower() for item in outline)


def test_sp6_out02_keep_strong_outline():
    nodes, edges, sk = _chain_skeleton()
    outline = build_rewrite_outline(sk)
    assert any(item["kind"] == "keep" for item in outline)


def test_sp6_api01_recompose_index_keys():
    nodes, edges, sk = _chain_skeleton()
    rc = recompose_index(nodes, edges, sk, fact_checker={"mode": "corpus"}, items_processed=1)
    for key in (
        "report_markdown",
        "verified_narrative",
        "rewrite_outline",
        "outline_count",
        "has_strong_narrative",
        "epsilon",
    ):
        assert key in rc
    assert rc["has_strong_narrative"] is True
    assert rc["epsilon"]["e2_report"] is True


def test_sp6_api01_epsilon_flags():
    nodes, edges, sk = _chain_skeleton()
    rc = recompose_index(nodes, edges, sk)
    eps = rc["epsilon"]
    assert eps["e3_narrative"] and eps["e4_rewrite_outline"]
