"""
하위 호환 shim — canonical: neo4j_utils.py
"""

from deconstructor.viz.neo4j_utils import (
    MAX_GRAPH_NODES,
    GraphEdge,
    GraphFetchResult,
    GraphNode,
    fetch_causal_graph,
)

# legacy name
fetch_full_graph = fetch_causal_graph

__all__ = [
    "MAX_GRAPH_NODES",
    "GraphEdge",
    "GraphFetchResult",
    "GraphNode",
    "fetch_causal_graph",
    "fetch_full_graph",
]
