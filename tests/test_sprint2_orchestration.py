"""
Sprint 2 — orchestration / cross-doc bridge (SP2-TEST-01).

See ``docs/design/SPRINT-2-orchestration-spec.md``.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.viz.neo4j_utils import GraphFetchResult, GraphNode
from deconstructor.web.corpus_bridge import (
    attach_bridge_edges,
    build_orchestration_meta,
    collect_corpus_fact_refs,
    compute_bridge_edges,
    normalize_subject,
)


def _fact(fid: str, subject: str, source_file: str) -> AtomicFact:
    return AtomicFact(
        id=fid,
        subject=subject,
        state_change="state -> changed",
        is_atomic=True,
        source_file=source_file,
        chunk_id=f"{source_file}#chunk-1/1",
    )


def _state(source_file: str, facts: list[AtomicFact]) -> dict:
    return {
        "source_document_meta": {"source_file": source_file},
        "completed_facts": facts,
    }


def test_sp2_brg02_normalize_subject():
    assert normalize_subject("  Ni  Catalyst ") == "ni catalyst"


def test_sp2_pol02_same_file_no_bridge():
    refs = collect_corpus_fact_refs(
        [
            _state("a.txt", [_fact("1", "Ni catalyst", "a.txt"), _fact("2", "Ni catalyst", "a.txt")]),
        ]
    )
    assert len(refs) == 2
    assert compute_bridge_edges(refs) == []


def test_sp2_brg03_cross_file_bridge():
    refs = collect_corpus_fact_refs(
        [
            _state("paper.pdf", [_fact("a1", "Ni catalyst", "paper.pdf")]),
            _state("memo.txt", [_fact("b1", "Ni Catalyst", "memo.txt")]),
        ]
    )
    bridges = compute_bridge_edges(refs)
    assert len(bridges) == 1
    assert bridges[0].edge_kind == "BRIDGE"
    assert {bridges[0].source_id, bridges[0].target_id} == {"a1", "b1"}


def test_sp2_mrg02_attach_bridge_edges():
    states = [
        _state("a.txt", [_fact("a1", "Grid power", "a.txt")]),
        _state("b.txt", [_fact("b1", "grid power", "b.txt")]),
    ]
    fetched = GraphFetchResult(
        nodes=[
            GraphNode(
                id="a1",
                subject="Grid power",
                state_change="off",
                timestamp=None,
                trigger_event="t",
                source_file="a.txt",
            ),
            GraphNode(
                id="b1",
                subject="grid power",
                state_change="off",
                timestamp=None,
                trigger_event="t",
                source_file="b.txt",
            ),
        ],
        edges=[],
        node_limit=2,
        truncated=False,
        total_nodes_in_db=None,
    )
    merged, bridges = attach_bridge_edges(fetched, states)
    assert len(bridges) == 1
    assert len(merged.edges) == 1
    assert merged.edges[0].edge_kind == "BRIDGE"


def test_sp2_ui01_orchestration_meta():
    states = [
        _state("a.txt", [_fact("a1", "X", "a.txt")]),
        _state("b.txt", [_fact("b1", "Y", "b.txt")]),
    ]
    meta = build_orchestration_meta(states, bridge_count=0)
    assert meta["merge_mode"] == "batch_corpus"
    assert meta["bridge_count"] == 0
    assert meta["cross_doc_label"] == "교차 0건"
    assert meta["source_file_count"] == 2

    cross_states = [
        _state("a.txt", [_fact("a1", "Same", "a.txt")]),
        _state("b.txt", [_fact("b1", "same", "b.txt")]),
    ]
    refs = collect_corpus_fact_refs(cross_states)
    meta2 = build_orchestration_meta(cross_states, bridge_count=len(compute_bridge_edges(refs)))
    assert meta2["bridge_count"] == 1
    assert meta2["cross_doc_label"] == "교차 1건"
