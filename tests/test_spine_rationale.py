"""μ-SPINE-01 — LinkRationale contract + mechanical R4/R6 generation."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from deconstructor.spine.contract import LinkRationale, SpineRecord
from deconstructor.spine.rationale import build_link_rationales
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "spine_design_sample.json"

_CAUSAL_RE = re.compile(r"(유발|때문에|causes|because)", re.IGNORECASE)

NODES = {
    "fact-a": {
        "subject": "Ni 촉매",
        "state_change": "CH4 생성 촉진",
        "reasoning": "금속-Ni 활성점에서 C-O 해리 후 메탄 경로가 우세해진다.",
    },
    "fact-b": {
        "subject": "CH4 생성",
        "state_change": "메탄 농도 상승",
    },
    "fact-c": {
        "subject": "메탄 수율",
        "state_change": "수율 지표 상승",
    },
    "fact-x": {
        "subject": "촉매 A",
        "state_change": "표면 활성 변화",
        "source_file": "paper_a.txt",
    },
    "fact-y": {
        "subject": "촉매 B",
        "state_change": "표면 활성 변화",
        "source_file": "paper_b.txt",
    },
}

EDGES = [
    {"source_fact_id": "fact-a", "target_fact_id": "fact-b", "edge_kind": "CAUSES"},
    {"source_fact_id": "fact-b", "target_fact_id": "fact-c", "edge_kind": "CAUSES"},
    {"source_fact_id": "fact-x", "target_fact_id": "fact-y", "edge_kind": "BRIDGE"},
]


def test_link_rationale_round_trip():
    raw = {
        "source_fact_id": "fact-a",
        "target_fact_id": "fact-b",
        "edge_kind": "CAUSES",
        "link_sentence": "Ni 촉매에서 CH4 생성이 촉진된다.",
        "link_mechanism": "금속-Ni 활성점.",
        "locale": "ko",
    }
    rec = LinkRationale.from_dict(raw)
    assert rec.to_dict() == raw


def test_spine_record_round_trip():
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    raw = sample["contract_sample"]["spine"]["spines"][0]
    rec = SpineRecord.from_dict(raw)
    assert rec.spine_id == raw["spine_id"]
    assert rec.to_dict()["node_ids"] == raw["node_ids"]


def test_build_link_rationales_causes_include_subjects():
    rationales = build_link_rationales(NODES, EDGES[:2], locale="ko")
    assert len(rationales) == 2
    for r in rationales:
        assert r.edge_kind == "CAUSES"
        assert r.link_sentence
        assert r.source_fact_id in NODES
        src_subj = NODES[r.source_fact_id]["subject"]
        tgt_subj = NODES[r.target_fact_id]["subject"]
        assert src_subj in r.link_sentence
        assert tgt_subj in r.link_sentence
        assert len(r.link_sentence) <= 120


def test_build_link_rationales_bridge_mechanism_empty_no_causal_verbs():
    rationales = build_link_rationales(NODES, EDGES[2:], locale="ko")
    assert len(rationales) == 1
    bridge = rationales[0]
    assert bridge.edge_kind == "BRIDGE"
    assert bridge.link_mechanism == ""
    assert not _CAUSAL_RE.search(bridge.link_sentence)
    assert "촉매 A" in bridge.link_sentence
    assert "촉매 B" in bridge.link_sentence


def test_build_link_rationales_graph_types():
    nodes = [
        GraphNode(
            id="n1",
            subject="Grid power",
            state_change="turned off",
            timestamp=None,
            trigger_event=None,
        ),
        GraphNode(
            id="n2",
            subject="Factory supply",
            state_change="interrupted",
            timestamp=None,
            trigger_event=None,
        ),
    ]
    edges = [GraphEdge(source_id="n1", target_id="n2", probability=1.0, latency=None)]
    rationales = build_link_rationales(nodes, edges)
    assert len(rationales) == 1
    assert rationales[0].locale == "en"
    assert "Grid power" in rationales[0].link_sentence


def test_build_matches_design_sample_shape():
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    expected = sample["contract_sample"]["link_rationales"]
    rationales = build_link_rationales(NODES, EDGES[:2], locale="ko")
    assert len(rationales) == len(expected)
    for got, exp in zip(rationales, expected, strict=True):
        assert got.source_fact_id == exp["source_fact_id"]
        assert got.target_fact_id == exp["target_fact_id"]
        assert got.edge_kind == exp["edge_kind"]
        assert got.locale == exp["locale"]
        assert got.link_sentence
        assert "link_mechanism" in got.to_dict()
