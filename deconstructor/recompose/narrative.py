"""
Sprint 6 — ε-3 verified narrative from strong CAUSES chains (SP6-NAR-01~03).
"""

from __future__ import annotations

from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

_EMPTY_NARRATIVE = "(No verified CAUSES chains with length ≥2 — ε-3 narrative empty.)"


def _node_map(nodes: list[GraphNode]) -> dict[str, GraphNode]:
    return {n.id: n for n in nodes}


def _format_chain_line(node_by_id: dict[str, GraphNode], node_ids: list[str]) -> str:
    """One strong chain → single prose line (NAR-01)."""
    parts: list[str] = []
    for i, nid in enumerate(node_ids):
        node = node_by_id.get(nid)
        if not node:
            continue
        label = f"{node.subject} ({node.state_change})"
        if i == 0:
            parts.append(label)
        else:
            parts.append(f"therefore {label}")
    if not parts:
        return ""
    if len(parts) == 1:
        return f"Verified fact: {parts[0]}."
    return "Because " + ", ".join(parts) + "."


def build_verified_narrative(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    skeleton: dict,
) -> str:
    """
    Build ε-3 narrative from skeleton strong chains (NAR-02: CAUSES, len≥2).

    ``edges`` reserved for future bridge annotation; chains come from skeleton.
    """
    _ = edges
    node_by_id = _node_map(nodes)
    chains = skeleton.get("strong_chains") or []
    lines: list[str] = []

    for ch in chains:
        node_ids = ch.get("node_ids") or []
        if len(node_ids) < 3:
            continue
        line = _format_chain_line(node_by_id, node_ids)
        if line:
            lines.append(line)

    if not lines:
        return _EMPTY_NARRATIVE
    return "\n\n".join(lines)
