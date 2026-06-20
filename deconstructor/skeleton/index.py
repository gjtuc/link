"""
Sprint 4 (G-SKP-INDEX) — skeleton_index orchestration (SP4-IDX-01, OUT-*).

Post-pipeline only — no Weaver/Skeptic changes.
"""

from __future__ import annotations

from collections import defaultdict, deque

from deconstructor.skeleton import rules
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode


def _build_outline(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    gap_ids: set[str],
    strong_ids: set[str],
    weak_ids: set[str],
) -> list[dict]:
    """Claim tree entries from CAUSES DAG (OUT-01, OUT-02)."""
    node_by_id = {n.id: n for n in nodes}
    c_edges = rules.causes_edges(edges)
    in_d, _out_d = rules.causes_degrees(set(node_by_id), c_edges)
    children: dict[str, list[str]] = defaultdict(list)
    for e in c_edges:
        if e.source_id in node_by_id and e.target_id in node_by_id:
            children[e.source_id].append(e.target_id)

    roots = sorted(nid for nid in node_by_id if in_d.get(nid, 0) == 0)
    if not roots:
        roots = sorted(node_by_id)

    outline: list[dict] = []
    seen: set[str] = set()

    def role_for(nid: str) -> str:
        if nid in gap_ids:
            return "gap"
        if nid in strong_ids:
            return "strong"
        if nid in weak_ids:
            return "weak"
        return "other"

    for root in roots:
        queue: deque[tuple[str, int, str | None]] = deque([(root, 0, None)])
        while queue:
            nid, depth, parent_id = queue.popleft()
            if nid in seen:
                continue
            seen.add(nid)
            node = node_by_id.get(nid)
            if not node:
                continue
            outline.append(
                {
                    "id": nid,
                    "subject": node.subject,
                    "state_change": node.state_change,
                    "role": role_for(nid),
                    "depth": depth,
                    "parent_id": parent_id,
                }
            )
            for child in sorted(children.get(nid, [])):
                if child not in seen:
                    queue.append((child, depth + 1, nid))

    for node in sorted(nodes, key=lambda n: (n.subject.lower(), n.id)):
        if node.id not in seen:
            outline.append(
                {
                    "id": node.id,
                    "subject": node.subject,
                    "state_change": node.state_change,
                    "role": role_for(node.id),
                    "depth": 0,
                    "parent_id": None,
                }
            )
    return outline


def skeleton_index(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> dict:
    """
    Compute Gap/Strong/Weak skeleton index + outline for UI/API.

    Returns JSON-serializable dict (API-01).
    """
    gaps = rules.find_gaps(nodes, edges)
    gap_ids = {g["id"] for g in gaps}
    strong_chains = rules.find_strong_chains(nodes, edges)
    strong_ids = rules.strong_node_ids(strong_chains)
    weak = rules.find_weak(nodes, edges, gap_ids=gap_ids, strong_ids=strong_ids)
    weak_ids = {w["id"] for w in weak}
    c_edges = rules.causes_edges(edges)

    outline = _build_outline(
        nodes,
        edges,
        gap_ids=gap_ids,
        strong_ids=strong_ids,
        weak_ids=weak_ids,
    )

    return {
        "gap_count": len(gaps),
        "strong_chain_count": len(strong_chains),
        "weak_count": len(weak),
        "gaps": gaps,
        "strong_chains": strong_chains,
        "weak": weak,
        "outline": outline,
        "health_summary": {
            "gap_count": len(gaps),
            "strong_chain_count": len(strong_chains),
            "weak_count": len(weak),
            "node_count": len(nodes),
            "causes_edge_count": len(c_edges),
        },
    }
