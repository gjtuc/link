"""μ-SPINE-02 — spine index / main path (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.spine.index import build_spine_records
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE_A = FIXTURES / "spine_index_a.json"


def _node(nid: str, subject: str, **kwargs) -> GraphNode:
    return GraphNode(
        id=nid,
        subject=subject,
        state_change=kwargs.get("state_change", ""),
        timestamp=None,
        trigger_event=None,
        source_file=kwargs.get("source_file"),
    )


def _edge(src: str, tgt: str, kind: str = "CAUSES") -> GraphEdge:
    return GraphEdge(source_id=src, target_id=tgt, probability=1.0, latency=None, edge_kind=kind)


def test_fixture_a_three_edge_chain():
    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    edges = data["edges"]
    spines = build_spine_records(nodes, edges)
    exp = data["expected"]
    assert len(spines) >= exp["min_spines"]
    first = spines[0]
    assert first.index == exp["first_index"]
    assert "→" in first.label
    assert first.is_branched is exp["is_branched"]
    assert len(first.main_path_node_ids) == exp["main_path_len"]
    assert set(first.main_path_node_ids).issubset(set(first.node_ids))


def test_single_edge_produces_no_spines():
    nodes = [_node("a", "A"), _node("b", "B")]
    edges = [_edge("a", "b")]
    assert build_spine_records(nodes, edges) == []


def test_bridge_in_spine_sets_bridge_count_and_label():
    nodes = [
        _node("a", "촉매 A", source_file="paper_a.pdf"),
        _node("b", "CH4", source_file="paper_a.pdf"),
        _node("c", "수율", source_file="paper_a.pdf"),
        _node("x", "촉매 B", source_file="paper_b.pdf"),
    ]
    edges = [
        _edge("a", "b"),
        _edge("b", "c"),
        _edge("b", "x", "BRIDGE"),
    ]
    spines = build_spine_records(nodes, edges)
    assert spines
    top = spines[0]
    assert top.bridge_count >= 1
    assert "(교차" in top.label


def test_branched_dag_main_path_subset():
    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    spines = build_spine_records(data["nodes"], data["edges"])
    spine = spines[0]
    assert spine.is_branched is True
    assert set(spine.main_path_node_ids).issubset(set(spine.node_ids))
    assert len(spine.node_ids) > len(spine.main_path_node_ids)


def test_spine_id_stable_for_same_main_path():
    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    first = build_spine_records(data["nodes"], data["edges"])
    second = build_spine_records(data["nodes"], data["edges"])
    assert first[0].spine_id == second[0].spine_id
