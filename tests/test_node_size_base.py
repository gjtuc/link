"""노드 크기 — 단순 고정 크기."""

from deconstructor.storm.viz_style import DEFAULT_NODE_SIZE
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode
from deconstructor.viz.visualizer import NODE_SIZE, build_pyvis_network


def test_all_nodes_same_fixed_size():
    nodes = [
        GraphNode("e1", "원숭이", "ate", "2026-01-01T10:00:00", "h", "extracted", "active"),
        GraphNode(
            "d1",
            "사육장 내 바나나 향",
            "scent",
            "2026-01-01T10:01:00",
            "h",
            "inferred",
            "dropped",
        ),
    ]
    net = build_pyvis_network(nodes, [])
    by_id = {n["id"]: n for n in net.nodes}
    assert by_id["e1"]["size"] == NODE_SIZE
    assert by_id["d1"]["size"] == NODE_SIZE
    assert by_id["e1"]["size"] == by_id["d1"]["size"]
    assert "dc_circle_r" not in by_id["e1"]


def test_hub_does_not_change_size():
    nodes = [
        GraphNode("e1", "A", "x", "2026-01-01T10:00:00", "h", "extracted", "active"),
        GraphNode("e2", "B", "y", "2026-01-01T10:01:00", "h", "extracted", "active"),
        GraphNode("hub", "C hub", "z", "2026-01-01T10:05:00", "h", "extracted", "active"),
    ]
    edges = [
        GraphEdge("e1", "hub", 1.0, 1000),
        GraphEdge("e2", "hub", 1.0, 2000),
    ]
    net = build_pyvis_network(nodes, edges)
    by_id = {n["id"]: n for n in net.nodes}
    assert by_id["hub"]["size"] == by_id["e1"]["size"] == DEFAULT_NODE_SIZE
