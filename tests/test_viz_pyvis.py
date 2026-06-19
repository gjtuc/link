"""
Step 3 visualizer — pyvis HTML 렌더링 단위 테스트
"""

from pathlib import Path

from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import render_to_html


def test_render_to_html_creates_file(tmp_path):
    nodes = [
        GraphNode("a", "grid", "power -> off", "2026-01-01T10:00:00", "headline"),
        GraphNode("b", "factory", "power -> lost", "2026-01-01T10:02:00", "headline"),
    ]
    edges = [GraphEdge("a", "b", 0.9, 120000)]
    out = tmp_path / "graph_output.html"
    path = render_to_html(nodes, edges, out)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "grid" in text
    assert "power" in text and "off" in text
    assert "vis.Network" in text or "pyvis" in text.lower()
    assert "physics" in text.lower()
