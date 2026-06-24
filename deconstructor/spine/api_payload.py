"""
STAGE 0-SPINE — μ-SPINE-02-API
계약: docs/design/BRANCH-SPINE-spec.md
선행: build_spine_records + build_link_rationales (μ-SPINE-01/02)
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from deconstructor.spine.index import build_spine_records
from deconstructor.spine.rationale import build_link_rationales
from deconstructor.viz.neo4j_utils import GraphEdge

DEFAULT_SPINE_FILTERS = {
    "include_hypothesis": False,
    "include_bridge": True,
}


def _relevant_edges(edges: Sequence[Any]) -> list[Any]:
    out: list[Any] = []
    for edge in edges:
        if isinstance(edge, GraphEdge):
            kind = (edge.edge_kind or "CAUSES").upper()
        else:
            kind = str(edge.get("edge_kind") or "CAUSES").upper()
        if kind in ("CAUSES", "BRIDGE"):
            out.append(edge)
    return out


def build_spine_payload(
    nodes: Mapping[str, Any] | Sequence[Any],
    edges: Sequence[Any],
) -> dict[str, Any]:
    """Analyze result ``spine`` block — longest main_path spine auto-selected."""
    records = build_spine_records(nodes, edges)
    spines = [rec.to_dict() for rec in records]
    selected = records[0].spine_id if records else ""
    return {
        "spines": spines,
        "selected_spine_id": selected,
        "filters": dict(DEFAULT_SPINE_FILTERS),
    }


def _normalize_edge_for_rationale(edge: Any) -> Any:
    if isinstance(edge, dict) and "source_id" in edge and "source_fact_id" not in edge:
        return {
            **edge,
            "source_fact_id": edge["source_id"],
            "target_fact_id": edge["target_id"],
        }
    return edge


def build_link_rationales_payload(
    nodes: Mapping[str, Any] | Sequence[Any],
    edges: Sequence[Any],
) -> list[dict[str, Any]]:
    """Analyze result ``link_rationales`` list (CAUSES + BRIDGE edges)."""
    relevant = [_normalize_edge_for_rationale(e) for e in _relevant_edges(edges)]
    return [rec.to_dict() for rec in build_link_rationales(nodes, relevant)]
