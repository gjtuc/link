"""
STAGE 0-SPINE — μ-SPINE-02
계약: docs/design/BRANCH-SPINE-spec.md
철학: §1f spine 목록 — find_strong_chains + BRIDGE + DAG 주 경로
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Mapping, Sequence

from deconstructor.skeleton.rules import find_strong_chains
from deconstructor.spine.contract import SpineRecord
from deconstructor.spine.main_path import longest_causes_path
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

MAX_SPINES = 20


def _as_graph_nodes(nodes: Mapping[str, Any] | Sequence[Any]) -> list[GraphNode]:
    if isinstance(nodes, Mapping):
        out: list[GraphNode] = []
        for key, value in nodes.items():
            if isinstance(value, GraphNode):
                out.append(value)
            else:
                item = dict(value)
                out.append(
                    GraphNode(
                        id=str(key),
                        subject=str(item.get("subject") or ""),
                        state_change=str(item.get("state_change") or ""),
                        timestamp=item.get("timestamp"),
                        trigger_event=item.get("trigger_event"),
                        source_file=item.get("source_file"),
                    )
                )
        return out
    out: list[GraphNode] = []
    for item in nodes:
        if isinstance(item, GraphNode):
            out.append(item)
        elif isinstance(item, dict):
            out.append(
                GraphNode(
                    id=str(item["id"]),
                    subject=str(item.get("subject") or ""),
                    state_change=str(item.get("state_change") or ""),
                    timestamp=item.get("timestamp"),
                    trigger_event=item.get("trigger_event"),
                    source_file=item.get("source_file"),
                )
            )
        else:
            raise TypeError(f"unsupported node entry: {type(item)!r}")
    return out


def _normalize_edges(edges: Sequence[Any]) -> list[GraphEdge]:
    normalized: list[GraphEdge] = []
    for edge in edges:
        if isinstance(edge, GraphEdge):
            normalized.append(edge)
        elif isinstance(edge, dict):
            normalized.append(
                GraphEdge(
                    source_id=str(edge["source_id"]),
                    target_id=str(edge["target_id"]),
                    probability=float(edge.get("probability", 1.0)),
                    latency=edge.get("latency"),
                    edge_kind=str(edge.get("edge_kind") or "CAUSES"),
                )
            )
        else:
            raise TypeError(f"unsupported edge entry: {type(edge)!r}")
    return normalized


def _split_edges(edges: list[GraphEdge]) -> tuple[list[GraphEdge], list[GraphEdge]]:
    causes = [e for e in edges if (e.edge_kind or "CAUSES") == "CAUSES"]
    bridges = [e for e in edges if (e.edge_kind or "CAUSES") == "BRIDGE"]
    return causes, bridges


def _expand_spine_nodes(
    core: tuple[str, ...],
    allowed: set[str],
    causes: list[GraphEdge],
    bridges: list[GraphEdge],
) -> set[str]:
    spine = set(core)
    while True:
        added = False
        for edge in bridges:
            if edge.source_id in spine and edge.target_id in allowed and edge.target_id not in spine:
                spine.add(edge.target_id)
                added = True
            if edge.target_id in spine and edge.source_id in allowed and edge.source_id not in spine:
                spine.add(edge.source_id)
                added = True
        if not added:
            break
    while True:
        added = False
        for edge in causes:
            if edge.source_id in spine and edge.target_id in allowed and edge.target_id not in spine:
                spine.add(edge.target_id)
                added = True
            if edge.target_id in spine and edge.source_id in allowed and edge.source_id not in spine:
                spine.add(edge.source_id)
                added = True
        if not added:
            break
    return spine


def _spine_edges(spine_nodes: set[str], edges: list[GraphEdge]) -> list[GraphEdge]:
    return [
        e
        for e in edges
        if e.source_id in spine_nodes and e.target_id in spine_nodes
    ]


def _stable_spine_id(main_path: tuple[str, ...]) -> str:
    digest = hashlib.sha256("|".join(main_path).encode("utf-8")).hexdigest()[:12]
    return f"spine-{digest}"


def _make_label(
    index: int,
    main_path: list[str],
    node_by_id: dict[str, GraphNode],
    bridge_count: int,
) -> str:
    start = node_by_id[main_path[0]].subject
    end = node_by_id[main_path[-1]].subject
    label = f"뼈대 {index} · {start} → {end}"
    if bridge_count > 0:
        label += f" (교차 {bridge_count})"
    return label


def build_spine_records(
    nodes: Mapping[str, Any] | Sequence[Any],
    edges: Sequence[Any],
    *,
    min_causes_edges: int = 2,
    max_spines: int = MAX_SPINES,
) -> list[SpineRecord]:
    """Enumerate spine DAGs from merged graph (strong chains + BRIDGE extension)."""
    graph_nodes = _as_graph_nodes(nodes)
    graph_edges = _normalize_edges(edges)
    node_by_id = {n.id: n for n in graph_nodes}
    allowed = set(node_by_id)
    causes, bridges = _split_edges(graph_edges)

    candidates: list[tuple[tuple[int, float], set[str], list[str], list[GraphEdge]]] = []
    seen_nodes: set[frozenset[str]] = set()

    for chain in find_strong_chains(graph_nodes, graph_edges, min_edges=min_causes_edges):
        core = tuple(chain["node_ids"])
        spine_nodes = _expand_spine_nodes(core, allowed, causes, bridges)
        key = frozenset(spine_nodes)
        if key in seen_nodes:
            continue
        seen_nodes.add(key)

        spine_edge_list = _spine_edges(spine_nodes, graph_edges)
        causes_pairs = [
            (e.source_id, e.target_id)
            for e in spine_edge_list
            if (e.edge_kind or "CAUSES") == "CAUSES"
        ]
        main_path = longest_causes_path(spine_nodes, causes_pairs)
        if len(main_path) - 1 < min_causes_edges:
            continue

        bridge_count = sum(1 for e in spine_edge_list if (e.edge_kind or "CAUSES") == "BRIDGE")
        total_edges = len(spine_edge_list)
        causes_count = len(causes_pairs)
        causes_ratio = causes_count / total_edges if total_edges else 0.0
        sort_key = (-len(main_path), -causes_ratio)
        candidates.append((sort_key, spine_nodes, main_path, spine_edge_list))

    candidates.sort(key=lambda item: item[0])

    records: list[SpineRecord] = []
    for idx, (_, spine_nodes, main_path, spine_edge_list) in enumerate(candidates[:max_spines], start=1):
        bridge_count = sum(1 for e in spine_edge_list if (e.edge_kind or "CAUSES") == "BRIDGE")
        main_tuple = tuple(main_path)
        records.append(
            SpineRecord(
                spine_id=_stable_spine_id(main_tuple),
                index=idx,
                label=_make_label(idx, main_path, node_by_id, bridge_count),
                bridge_count=bridge_count,
                node_ids=tuple(sorted(spine_nodes, key=lambda nid: (main_path.index(nid) if nid in main_path else 999, nid))),
                edge_ids=tuple((e.source_id, e.target_id) for e in spine_edge_list),
                main_path_node_ids=main_tuple,
                is_branched=len(spine_nodes) > len(main_path),
            )
        )
    return records
