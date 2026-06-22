"""
Q1 — 2-pass Dreamer pass-2 source fact selection (μ-Q1-02).

Reuses ``skeleton.rules.find_gaps`` for Gap nodes (option A).
"""

from __future__ import annotations

from collections import defaultdict

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.skeleton.rules import find_gaps
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode


def _causes_edges(edges: list[CausalEdge]) -> list[CausalEdge]:
    return list(edges)


def _degrees(
    node_ids: set[str],
    edges: list[CausalEdge],
) -> tuple[dict[str, int], dict[str, int]]:
    in_d: dict[str, int] = defaultdict(int)
    out_d: dict[str, int] = defaultdict(int)
    for e in edges:
        if e.source_fact_id in node_ids:
            out_d[e.source_fact_id] += 1
        if e.target_fact_id in node_ids:
            in_d[e.target_fact_id] += 1
    return dict(in_d), dict(out_d)


def _interior_node_ids(edges: list[CausalEdge]) -> set[str]:
    """Nodes with both incoming and outgoing CAUSES — chain middle, not 양끝."""
    endpoint_ids: set[str] = set()
    for e in edges:
        endpoint_ids.add(e.source_fact_id)
        endpoint_ids.add(e.target_fact_id)
    if not endpoint_ids:
        return set()
    in_d, out_d = _degrees(endpoint_ids, edges)
    return {
        nid
        for nid in endpoint_ids
        if in_d.get(nid, 0) > 0 and out_d.get(nid, 0) > 0
    }


def _chain_endpoint_ids(edges: list[CausalEdge]) -> set[str]:
    """Per-edge source/target minus interior (middle of A→B→C)."""
    c_edges = _causes_edges(edges)
    endpoint_ids: set[str] = set()
    for e in c_edges:
        endpoint_ids.add(e.source_fact_id)
        endpoint_ids.add(e.target_fact_id)
    return endpoint_ids - _interior_node_ids(c_edges)


def facts_to_graph_nodes(facts: list[AtomicFact]) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    for f in facts:
        nodes.append(
            GraphNode(
                id=f.id,
                subject=f.subject,
                state_change=f.state_change,
                timestamp=f.timestamp.isoformat() if f.timestamp else None,
                trigger_event="",
                source_type=f.source_type or "extracted",
                check_status=f.check_status or "active",
            )
        )
    return nodes


def edges_to_graph_edges(edges: list[CausalEdge]) -> list[GraphEdge]:
    return [
        GraphEdge(
            source_id=e.source_fact_id,
            target_id=e.target_fact_id,
            probability=e.probability,
            latency=e.latency,
            edge_kind="CAUSES",
        )
        for e in edges
    ]


def compute_pass2_gaps(
    completed_facts: list[AtomicFact],
    verified_edges: list[CausalEdge],
) -> list[dict]:
    """Gap list from pass1 extracted graph — ``find_gaps`` reuse."""
    nodes = facts_to_graph_nodes(completed_facts)
    g_edges = edges_to_graph_edges(verified_edges)
    return find_gaps(nodes, g_edges)


def select_pass2_source_facts(
    completed_facts: list[AtomicFact],
    verified_edges: list[CausalEdge],
    *,
    gap_nodes: list[dict] | None = None,
) -> list[AtomicFact]:
    """
    Pass-2 Dreamer sources: chain endpoints + Gap (option A).

    Excludes orphan extracted, interior nodes, non-extracted inferred.
    """
    fact_by_id = {f.id: f for f in completed_facts}
    extracted = [f for f in completed_facts if (f.source_type or "extracted") == "extracted"]
    extracted_ids = {f.id for f in extracted}

    c_edges = _causes_edges(verified_edges)
    endpoint_ids = _chain_endpoint_ids(c_edges)

    if gap_nodes is None:
        gap_nodes = compute_pass2_gaps(extracted, c_edges)
    gap_ids = {g["id"] for g in gap_nodes}

    selected: set[str] = set(endpoint_ids) | gap_ids

    ordered_ids = sorted(
        selected,
        key=lambda i: (fact_by_id[i].subject.lower(), i) if i in fact_by_id else (i, i),
    )
    result: list[AtomicFact] = []
    for fid in ordered_ids:
        f = fact_by_id.get(fid)
        if f is None:
            continue
        if (f.source_type or "extracted") != "extracted":
            continue
        result.append(f)
    return result
