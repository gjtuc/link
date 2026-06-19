"""범례 hover 강조 — HTML·노드 메타데이터."""

from pathlib import Path

from deconstructor.viz.legend import build_legend_html
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import build_pyvis_network, render_to_html


def test_build_legend_html_has_filter_items_and_highlight_script():
    html = build_legend_html()
    assert 'class="legend-filter-item"' in html
    assert 'data-filter="extracted"' in html
    assert 'data-filter="promoted"' in html
    assert 'data-filter="edge-dashed"' in html
    assert "__dcAttachLegendHighlight" in html
    assert "restoreNodeBaseline" in html
    assert "nodeBaselineOpacity" in html
    assert 'id="legend-side-toggle"' in html
    assert 'class="legend-title-chevron"' in html
    assert "범례 ▾" not in html
    assert "범례 ▸" not in html


def test_pyvis_nodes_carry_legend_class():
    nodes = [
        GraphNode("e1", "A", "x", "2026-01-01T10:00:00", "h", "extracted", "active"),
        GraphNode("i1", "B", "y", "2026-01-01T10:01:00", "h", "inferred", "pending"),
        GraphNode(
            "p1",
            "C",
            "z",
            "2026-01-01T10:02:00",
            "h",
            "inferred",
            "promoted",
        ),
    ]
    edges = [
        GraphEdge("e1", "i1", 1.0, 1000),
        GraphEdge("i1", "p1", 1.0, 2000),
    ]
    net = build_pyvis_network(nodes, edges)
    by_id = {n["id"]: n for n in net.nodes}

    assert by_id["e1"]["legend_class"] == "extracted"
    assert by_id["i1"]["legend_class"] == "inferred"
    assert by_id["p1"]["legend_class"] == "promoted"

    edge = net.edges[0]
    assert edge.get("legend_class") in ("edge-solid", "edge-dashed")


def test_render_html_hides_pyvis_heading_and_fills_height(tmp_path: Path):
    nodes = [
        GraphNode("n1", "solo", "s", "2026-01-01T10:00:00", "h", "extracted", "active"),
    ]
    path = render_to_html(nodes, [], tmp_path / "g.html")
    text = path.read_text(encoding="utf-8")
    assert "deconstructor-graph-embed" in text
    assert "vis-tooltip" in text
    assert "pre-line" in text
    assert "__dcGraphNetwork" in text
    assert "anchor_hover_only" in text
    assert "hoverNode" in text
