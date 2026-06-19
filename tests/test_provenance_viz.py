"""Step 1 — Provenance → Pyvis 스타일 맵·HTML 렌더링 테스트."""

from pathlib import Path

from deconstructor.provenance.viz_style import (
    COLOR_EXTRACTED,
    COLOR_INFERRED,
    COLOR_VERIFIED,
    resolve_edge_style,
    resolve_node_style,
)
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import render_to_html


def test_resolve_node_style_extracted_blue():
    style = resolve_node_style("extracted", "active")
    assert style.color == COLOR_EXTRACTED
    assert style.opacity == 1.0
    assert style.label_prefix == ""


def test_resolve_node_style_verified_green():
    style = resolve_node_style("verified", "active")
    assert style.color == COLOR_VERIFIED


def test_resolve_node_style_promoted_inferred_yellow_green_border():
    style = resolve_node_style("inferred", "promoted")
    assert style.color == COLOR_INFERRED
    assert style.border_color == COLOR_VERIFIED
    assert style.border_width == 3


def test_resolve_node_style_ghost_dropped_yellow_x():
    style = resolve_node_style("inferred", "dropped")
    assert style.color == COLOR_INFERRED
    assert style.opacity == 0.4
    assert style.label_prefix == "✖ "


def test_resolve_edge_style_dashed_for_inferred():
    estyle = resolve_edge_style(
        source_type="extracted",
        target_type="inferred",
        target_check_status="pending",
        probability=0.5,
    )
    assert estyle.dashes is True


def test_resolve_edge_style_solid_for_promoted_inferred():
    estyle = resolve_edge_style(
        source_type="extracted",
        target_type="inferred",
        target_check_status="promoted",
        probability=0.9,
    )
    assert estyle.dashes is False


def test_resolve_edge_style_solid_for_verified_causal():
    estyle = resolve_edge_style(
        source_type="extracted",
        target_type="verified",
        target_check_status="active",
        probability=0.9,
    )
    assert estyle.dashes is False


def test_render_html_contains_provenance_markers(tmp_path: Path):
    nodes = [
        GraphNode("e1", "grid", "off", "2026-01-01T10:00:00", "h", "extracted", "active"),
        GraphNode("i1", "supply", "cut", "2026-01-01T10:05:00", "h", "inferred", "dropped"),
        GraphNode("p1", "supply", "restored", "2026-01-01T10:08:00", "h", "inferred", "promoted"),
    ]
    edges = [
        GraphEdge("e1", "p1", 0.95, 60000),
        GraphEdge("e1", "i1", 0.3, 120000),
    ]
    path = render_to_html(nodes, edges, tmp_path / "prov.html")
    text = path.read_text(encoding="utf-8")
    assert "grid" in text
    assert "✖" in text or "supply" in text
    assert COLOR_VERIFIED.replace("#", "") in text or "06d6a0" in text.lower()
    assert "physics" in text.lower()
