"""
Sprint 4 — skeleton classification rules (SP4-IDX-02~04).

γ mapping: Gap / Strong / Weak — see STAGE-0-1 and SPRINT-4-skeleton-ui-spec.md.
"""

from __future__ import annotations

import re
from collections import defaultdict

from deconstructor.provenance.types import is_promoted_inferred
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

MAX_STRONG_CHAINS = 50

_CONCLUSION_KEYWORDS = (
    "increased",
    "decreased",
    "rose",
    "fell",
    "result",
    "achieved",
    "improved",
    "reduced",
    "grew",
    "declined",
    "higher",
    "lower",
    "상승",
    "하락",
    "증가",
    "감소",
    "결과",
    "달성",
)
_CONCLUSION_RE = re.compile(
    "|".join(re.escape(k) for k in _CONCLUSION_KEYWORDS),
    re.IGNORECASE,
)


def causes_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    """CAUSES only — BRIDGE excluded from Gap/Strong (IDX-05)."""
    return [e for e in edges if (e.edge_kind or "CAUSES") == "CAUSES"]


def causes_degrees(
    node_ids: set[str],
    edges: list[GraphEdge],
) -> tuple[dict[str, int], dict[str, int]]:
    in_d: dict[str, int] = defaultdict(int)
    out_d: dict[str, int] = defaultdict(int)
    for e in edges:
        if e.source_id in node_ids:
            out_d[e.source_id] += 1
        if e.target_id in node_ids:
            in_d[e.target_id] += 1
    return dict(in_d), dict(out_d)


def has_conclusion_keyword(state_change: str) -> bool:
    return bool(_CONCLUSION_RE.search(state_change or ""))


def is_conclusion_like(node: GraphNode, in_deg: int, out_deg: int) -> bool:
    """
    SP4-IDX-02 heuristic — see spec μ-IDX-02.

    Leaf (out=0), downstream 因 (out>0), or outcome keyword in state_change.
    """
    if out_deg > 0:
        return True
    if has_conclusion_keyword(node.state_change):
        return True
    return out_deg == 0


def gap_reason(node: GraphNode, in_deg: int, out_deg: int) -> str:
    if out_deg > 0 and in_deg == 0:
        return "unsupported_cause"
    if has_conclusion_keyword(node.state_change):
        return "outcome_without_cause"
    return "orphan_conclusion"


def find_gaps(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> list[dict]:
    """Gap nodes: conclusion-like with CAUSES in-degree 0."""
    node_by_id = {n.id: n for n in nodes}
    node_ids = set(node_by_id)
    c_edges = causes_edges(edges)
    in_d, out_d = causes_degrees(node_ids, c_edges)

    gaps: list[dict] = []
    for nid, node in node_by_id.items():
        i = in_d.get(nid, 0)
        o = out_d.get(nid, 0)
        if i == 0 and is_conclusion_like(node, i, o):
            gaps.append(
                {
                    "id": nid,
                    "subject": node.subject,
                    "state_change": node.state_change,
                    "reason": gap_reason(node, i, o),
                }
            )
    gaps.sort(key=lambda g: (g["subject"].lower(), g["id"]))
    return gaps


def find_strong_chains(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    min_edges: int = 2,
) -> list[dict]:
    """
    Verified CAUSES paths with at least ``min_edges`` consecutive edges (SP4-IDX-03).
    """
    node_by_id = {n.id: n for n in nodes}
    c_edges = causes_edges(edges)
    adj: dict[str, list[str]] = defaultdict(list)
    for e in c_edges:
        if e.source_id in node_by_id and e.target_id in node_by_id:
            adj[e.source_id].append(e.target_id)

    chains: list[tuple[str, ...]] = []

    def dfs(path: list[str], current: str, depth: int) -> None:
        if depth >= min_edges:
            chains.append(tuple(path))
            if len(chains) >= MAX_STRONG_CHAINS:
                return
        for nxt in adj.get(current, []):
            if nxt in path:
                continue
            path.append(nxt)
            dfs(path, nxt, depth + 1)
            path.pop()
            if len(chains) >= MAX_STRONG_CHAINS:
                return

    for start in sorted(node_by_id):
        dfs([start], start, 0)

    # Prefer longer chains; dedupe by full tuple
    seen: set[tuple[str, ...]] = set()
    result: list[dict] = []
    for chain in sorted(chains, key=lambda c: (-len(c), c)):
        if chain in seen:
            continue
        if len(chain) - 1 < min_edges:
            continue
        seen.add(chain)
        labels = [node_by_id[nid].subject for nid in chain]
        result.append(
            {
                "node_ids": list(chain),
                "labels": labels,
                "length": len(chain) - 1,
            }
        )
        if len(result) >= MAX_STRONG_CHAINS:
            break
    return result


def strong_node_ids(chains: list[dict]) -> set[str]:
    ids: set[str] = set()
    for ch in chains:
        ids.update(ch.get("node_ids") or [])
    return ids


def find_weak(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    gap_ids: set[str],
    strong_ids: set[str],
) -> list[dict]:
    """
    Weak nodes (γ partial): promoted inferred or orphan extracted, excluding gap/strong.
    """
    node_ids = {n.id for n in nodes}
    c_edges = causes_edges(edges)
    in_d, out_d = causes_degrees(node_ids, c_edges)
    endpoint_ids: set[str] = set()
    for e in c_edges:
        endpoint_ids.add(e.source_id)
        endpoint_ids.add(e.target_id)

    weak: list[dict] = []
    for node in nodes:
        if node.id in gap_ids or node.id in strong_ids:
            continue
        reason: str | None = None
        if is_promoted_inferred(node.source_type, node.check_status):
            reason = "promoted_hypothesis"
        elif node.source_type == "extracted" and node.id not in endpoint_ids:
            reason = "orphan_extracted"
        elif (
            node.id in endpoint_ids
            and in_d.get(node.id, 0) == 0
            and out_d.get(node.id, 0) == 1
            and not is_conclusion_like(node, 0, 1)
        ):
            reason = "single_edge_peripheral"
        if reason:
            weak.append(
                {
                    "id": node.id,
                    "subject": node.subject,
                    "state_change": node.state_change,
                    "reason": reason,
                }
            )
    weak.sort(key=lambda w: (w["subject"].lower(), w["id"]))
    return weak
