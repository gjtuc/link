"""
pyvis HTML 렌더링 단위 테스트
=============================

Neo4j 없이 GraphNode/GraphEdge 더미 데이터로 render_to_html 검증.
CI·오프라인에서 viz 레이어 회귀 방지.

관련 모듈:
  deconstructor.viz.pyvis_render — 실제 구현
  deconstructor.viz.export       — Neo4j + webbrowser (통합은 수동/--db)
"""

from pathlib import Path

from deconstructor.viz.neo4j_fetch import GraphEdge, GraphNode
from deconstructor.viz.pyvis_render import render_to_html


def test_render_to_html_creates_file(tmp_path):
    """HTML 파일 생성 및 pyvis/vis.js 마커 포함 여부."""
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
    assert "vis.Network" in text or "pyvis" in text.lower()
