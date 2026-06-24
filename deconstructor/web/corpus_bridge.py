"""
Sprint 2 (G-ORC-BRIDGE) — batch corpus cross-document bridge edges.

See ``docs/design/SPRINT-2-orchestration-spec.md`` (μ BRG-*, POL-02).

Bridge = **subject match across different source_file** — NOT Skeptic CAUSES.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deconstructor.viz.neo4j_utils import GraphEdge, GraphFetchResult

MAX_BRIDGE_EDGES = 30
MERGE_MODE_BATCH_CORPUS = "batch_corpus"


@dataclass(frozen=True)
class CorpusFactRef:
    fact_id: str
    norm_subject: str
    source_file: str
    chunk_id: str = ""


def normalize_subject(subject: str) -> str:
    """Case/space normalized subject key (μ BRG-02)."""
    return " ".join((subject or "").strip().lower().split())


def _source_file_for_fact(fact: Any, meta: dict[str, Any]) -> str:
    sf = getattr(fact, "source_file", None) or meta.get("source_file") or ""
    return str(sf).strip()


def collect_corpus_fact_refs(states: list[dict[str, Any]]) -> list[CorpusFactRef]:
    """Pipeline states → corpus pool (completed_facts only, μ BRG-01)."""
    refs: list[CorpusFactRef] = []
    for state in states:
        meta = dict(state.get("source_document_meta") or {})
        for fact in state.get("completed_facts") or []:
            subject = getattr(fact, "subject", "") or ""
            if not subject.strip():
                continue
            source_file = _source_file_for_fact(fact, meta)
            if not source_file:
                continue
            refs.append(
                CorpusFactRef(
                    fact_id=fact.id,
                    norm_subject=normalize_subject(subject),
                    source_file=source_file,
                    chunk_id=str(getattr(fact, "chunk_id", "") or ""),
                )
            )
    return refs


def compute_bridge_edges(
    refs: list[CorpusFactRef],
    *,
    max_edges: int = MAX_BRIDGE_EDGES,
) -> list[GraphEdge]:
    """
    Cross-doc bridge edges (μ BRG-03~04).

    Requires ≥2 distinct ``source_file`` per normalized subject.
    Star topology from lexicographically first file to others.
    """
    by_subject: dict[str, dict[str, CorpusFactRef]] = {}
    for ref in refs:
        if not ref.norm_subject:
            continue
        by_subject.setdefault(ref.norm_subject, {})
        # One representative fact per (subject, source_file)
        if ref.source_file not in by_subject[ref.norm_subject]:
            by_subject[ref.norm_subject][ref.source_file] = ref

    bridges: list[GraphEdge] = []
    seen_pairs: set[tuple[str, str]] = set()

    for file_map in by_subject.values():
        if len(file_map) < 2:
            continue
        files = sorted(file_map.keys())
        hub = file_map[files[0]]
        for other_file in files[1:]:
            other = file_map[other_file]
            pair = tuple(sorted((hub.fact_id, other.fact_id)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            bridges.append(
                GraphEdge(
                    source_id=hub.fact_id,
                    target_id=other.fact_id,
                    probability=0.0,
                    latency=None,
                    edge_kind="BRIDGE",
                )
            )
            if len(bridges) >= max_edges:
                return bridges
    return bridges


def distinct_source_files(refs: list[CorpusFactRef]) -> list[str]:
    return sorted({r.source_file for r in refs if r.source_file})


def build_orchestration_meta(
    states: list[dict[str, Any]],
    bridge_count: int,
) -> dict[str, Any]:
    """API ``orchestration`` block (μ UI-01~02)."""
    refs = collect_corpus_fact_refs(states)
    files = distinct_source_files(refs)
    label = f"교차 {bridge_count}건" if bridge_count else "교차 0건"
    return {
        "merge_mode": MERGE_MODE_BATCH_CORPUS,
        "bridge_count": bridge_count,
        "source_file_count": len(files),
        "source_files": files,
        "cross_doc_label": label,
    }


def attach_bridge_edges(
    fetched: GraphFetchResult,
    states: list[dict[str, Any]],
) -> tuple[GraphFetchResult, list[GraphEdge]]:
    """Append BRIDGE edges to graph fetch result (μ MRG-02)."""
    refs = collect_corpus_fact_refs(states)
    bridges = compute_bridge_edges(refs)
    if not bridges:
        return fetched, bridges

    node_ids = {n.id for n in fetched.nodes}
    valid = [e for e in bridges if e.source_id in node_ids and e.target_id in node_ids]
    if not valid:
        return fetched, []

    existing = {(e.source_id, e.target_id) for e in fetched.edges}
    merged_edges = list(fetched.edges)
    for edge in valid:
        key = (edge.source_id, edge.target_id)
        if key not in existing:
            existing.add(key)
            merged_edges.append(edge)

    return (
        GraphFetchResult(
            nodes=fetched.nodes,
            edges=merged_edges,
            node_limit=fetched.node_limit,
            truncated=fetched.truncated,
            total_nodes_in_db=fetched.total_nodes_in_db,
            trigger_events_filter=fetched.trigger_events_filter,
            analysis_run_id_filter=fetched.analysis_run_id_filter,
            matched_nodes_in_db=fetched.matched_nodes_in_db,
        ),
        valid,
    )
