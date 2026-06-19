"""Step 2 neo4j_utils — 노드 상한·엣지 필터 단위 테스트."""

from deconstructor.viz.neo4j_utils import MAX_GRAPH_NODES, GraphEdge, GraphNode


def test_max_graph_nodes_default_is_300():
    assert MAX_GRAPH_NODES == 300


def test_graph_node_tooltip_fields():
    """Step 3 툴팁에 필요한 필드가 dataclass에 존재."""
    n = GraphNode("id1", "grid", "off -> occurred", "2026-01-01T10:00:00", "headline")
    assert n.state_change == "off -> occurred"
    assert n.timestamp is not None


def test_graph_edge_is_verified_causal_only():
    """Rejected 는 DB에 없음 — GraphEdge = CAUSES 메타만."""
    e = GraphEdge("a", "b", 1.0, 120000)
    assert e.probability == 1.0
    assert e.latency == 120000
