"""Dreamer anchor — hidden edge + hover reveal."""

from deconstructor.viz.neo4j_utils import GraphNode
from deconstructor.viz.visualizer import _node_tooltip, build_pyvis_network


def test_inferred_has_hidden_anchor_edge():
    anchor = GraphNode(
        "src-1",
        "BZY10 bulk conductivity",
        "value -> increased",
        "2026-01-01T10:00:00",
        "h",
        "extracted",
        "active",
    )
    promoted = GraphNode(
        "inf-1",
        "fuel cell output",
        "power -> reduced",
        "2026-01-01T10:05:00",
        "h",
        "inferred",
        "promoted",
        anchor_fact_id="src-1",
        reasoning="Lower ionic conductivity reduces cell current.",
    )
    net = build_pyvis_network([anchor, promoted], [])
    anchor_edges = [e for e in net.edges if e.get("anchor_hover_only")]
    assert len(anchor_edges) == 1
    assert anchor_edges[0]["hidden"] is True
    assert anchor_edges[0]["dashes"] is True
    assert anchor_edges[0]["from"] == "src-1"
    assert anchor_edges[0]["to"] == "inf-1"

    by_id = {n["id"]: n for n in net.nodes}
    assert by_id["inf-1"].get("anchor_fact_id") == "src-1"


def test_inferred_tooltip_hints_hover_line_not_anchor_block():
    anchor = GraphNode(
        "src-1",
        "BZY10 bulk conductivity",
        "value -> increased",
        "2026-01-01T10:00:00",
        "h",
        "extracted",
        "active",
    )
    promoted = GraphNode(
        "inf-1",
        "fuel cell output",
        "power -> reduced",
        "2026-01-01T10:05:00",
        "h",
        "inferred",
        "promoted",
        anchor_fact_id="src-1",
        reasoning="Lower ionic conductivity reduces cell current.",
    )
    tip = _node_tooltip(promoted, node_by_id={anchor.id: anchor, promoted.id: promoted})
    assert "ripples from" not in tip
    assert "점선 화살표" in tip


def test_extracted_has_no_anchor_edge():
    node = GraphNode(
        "e1",
        "grid",
        "off",
        "2026-01-01T10:00:00",
        "h",
        "extracted",
        "active",
    )
    net = build_pyvis_network([node], [])
    assert not any(e.get("anchor_hover_only") for e in net.edges)
