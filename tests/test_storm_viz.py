"""Step 4 — Storm viz: critical style API + degree-based node sizing in graph."""

from pathlib import Path

from deconstructor.storm.viz_style import (
    COLOR_CRITICAL,
    CRITICAL_NODE_SIZE,
    DEFAULT_NODE_SIZE,
    MAX_NODE_SIZE,
    build_critical_pyvis_kwargs,
    format_critical_tooltip_prefix,
    resolve_critical_style,
    resolve_node_size_from_degree,
)
from deconstructor.provenance.viz_style import COLOR_VERIFIED, resolve_node_style
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import build_pyvis_network, render_to_html


def test_graph_node_storm_fields_defaults():
    node = GraphNode("n1", "grid", "off", "2026-01-01T10:00:00", "h")
    assert node.stress_level == 0
    assert node.is_critical is False


def test_resolve_critical_style_overrides_provenance():
    """Legacy storm API — graph viz uses provenance color + degree size instead."""
    provenance = resolve_node_style("verified", "active")
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


def test_resolve_node_size_from_degree_scales_with_connections():
    assert resolve_node_size_from_degree() == DEFAULT_NODE_SIZE
    assert resolve_node_size_from_degree(in_degree=1) == DEFAULT_NODE_SIZE
    assert resolve_node_size_from_degree(in_degree=2, out_degree=1) > DEFAULT_NODE_SIZE
    assert (
        resolve_node_size_from_degree(in_degree=20, out_degree=20) == MAX_NODE_SIZE
    )


def test_render_html_critical_node_keeps_provenance_grows_with_degree(tmp_path: Path):
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

    assert "e63946" not in text.lower()
    assert str(DEFAULT_NODE_SIZE) in text
    # pyvis title JSON escapes non-ASCII (연결 → \uc5f0\uacb0)
    assert "\\uc5f0\\uacb0" in text
    assert "stress: 70" in text


def test_build_pyvis_network_hub_larger_not_red():
    """
    연결 많은 hub는 크기만 커지고 provenance 색 유지 (빨강 override 없음).

    e1→c1, e2→c1: c1 in-degree=2 → size > e1
    """
    nodes = [
        GraphNode(
            "e1",
            "Trump",
            "signed MOU",
            "2026-01-01T10:00:00",
            "h",
            "extracted",
            "active",
        ),
        GraphNode(
            "e2",
            "EU",
            "sanctions",
            "2026-01-01T10:01:00",
            "h",
            "extracted",
            "active",
        ),
        GraphNode(
            "c1",
            "US and Iran",
            "negotiations",
            "2026-01-01T10:05:00",
            "h",
            "extracted",
            "active",
            stress_level=110,
            is_critical=True,
        ),
    ]
    edges = [
        GraphEdge("e1", "c1", 1.0, 60000),
        GraphEdge("e2", "c1", 1.0, 120000),
    ]
    net = build_pyvis_network(nodes, edges)

    cause = next(n for n in net.nodes if n["id"] == "e1")
    hub = next(n for n in net.nodes if n["id"] == "c1")

    def _node_bg(color):
        return color["background"] if isinstance(color, dict) else color

    assert _node_bg(cause["color"]) == "#8ecae6"
    if isinstance(cause["color"], dict):
        assert cause["color"]["border"] != COLOR_CRITICAL
    assert _node_bg(hub["color"]) == "#8ecae6"
    assert hub["size"] > cause["size"]


def test_build_pyvis_network_critical_keeps_provenance_color_not_red():
    node = GraphNode(
        "c1",
        "A공장",
        "output -> halted",
        "2026-01-01T10:05:00",
        "h",
        "verified",
        "active",
        stress_level=110,
        is_critical=True,
    )
    net = build_pyvis_network([node], [])
    node_data = net.nodes[0]

    assert node_data["size"] == DEFAULT_NODE_SIZE
    assert node_data.get("shadow") is not True
    color = node_data["color"]
    bg = color["background"] if isinstance(color, dict) else color
    assert bg == COLOR_VERIFIED
    assert bg != COLOR_CRITICAL


def test_build_critical_pyvis_kwargs_structure():
    style = resolve_critical_style(stress_level=99)
    kwargs = build_critical_pyvis_kwargs(
        label="A공장",
        tooltip=format_critical_tooltip_prefix(99),
        style=style,
    )
    assert kwargs["shadow"] is True
    assert kwargs["size"] == CRITICAL_NODE_SIZE
    assert kwargs["color"]["background"] == COLOR_CRITICAL
