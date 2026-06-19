"""Step 4 — Critical node Pyvis visualization tests."""

from pathlib import Path

from deconstructor.storm.viz_style import (
    COLOR_CRITICAL,
    CRITICAL_NODE_SIZE,
    build_critical_pyvis_kwargs,
    format_critical_tooltip_prefix,
    resolve_critical_style,
)
from deconstructor.provenance.viz_style import COLOR_VERIFIED, resolve_node_style
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import build_pyvis_network, render_to_html


def test_graph_node_storm_fields_defaults():
    node = GraphNode("n1", "grid", "off", "2026-01-01T10:00:00", "h")
    assert node.stress_level == 0
    assert node.is_critical is False


def test_resolve_critical_style_overrides_provenance():
    provenance = resolve_node_style("verified", "promoted")
    critical = resolve_critical_style(stress_level=110)

    assert provenance.color == COLOR_VERIFIED
    assert critical.color == COLOR_CRITICAL
    assert critical.size == CRITICAL_NODE_SIZE
    assert critical.shadow is True
    assert critical.font_color == "white"
    assert critical.font_bold is True


def test_format_critical_tooltip_prefix_contains_warning():
    prefix = format_critical_tooltip_prefix(70)
    assert "CRITICAL WARNING" in prefix
    assert "Stress Level: 70" in prefix
    assert COLOR_CRITICAL in prefix


def test_render_html_critical_node_red_large_shadow(tmp_path: Path):
    nodes = [
        GraphNode(
            "e1",
            "grid",
            "power -> off",
            "2026-01-01T10:00:00",
            "h",
            "extracted",
            "active",
            stress_level=30,
            is_critical=False,
        ),
        GraphNode(
            "t1",
            "A공장",
            "output -> halted",
            "2026-01-01T10:05:00",
            "h",
            "verified",
            "promoted",
            stress_level=70,
            is_critical=True,
        ),
    ]
    edges = [GraphEdge("e1", "t1", 0.9, 60000)]

    path = render_to_html(nodes, edges, tmp_path / "storm.html")
    text = path.read_text(encoding="utf-8")

    assert "ff0033" in text.lower()
    assert str(CRITICAL_NODE_SIZE) in text
    assert "shadow" in text.lower()
    assert "CRITICAL WARNING" in text
    assert "Stress Level: 70" in text
    assert "white" in text.lower()


def test_build_pyvis_network_critical_overrides_verified_color():
    node = GraphNode(
        "c1",
        "A공장",
        "output -> halted",
        "2026-01-01T10:05:00",
        "h",
        "verified",
        "promoted",
        stress_level=110,
        is_critical=True,
    )
    net = build_pyvis_network([node], [])
    node_data = net.nodes[0]

    assert node_data["size"] == CRITICAL_NODE_SIZE
    assert node_data.get("shadow") is True
    assert node_data["color"]["background"] == COLOR_CRITICAL
    assert node_data["font"]["color"] == "white"
    assert node_data["font"]["bold"] is True


def test_build_critical_pyvis_kwargs_structure():
    style = resolve_critical_style(stress_level=99)
    kwargs = build_critical_pyvis_kwargs(
        label="A공장",
        tooltip=format_critical_tooltip_prefix(99),
        style=style,
    )
    assert kwargs["shadow"] is True
    assert kwargs["size"] == 35
    assert kwargs["color"]["background"] == COLOR_CRITICAL
