"""μ-SPINE-02-API — analyze JSON spine + link_rationales payload (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.spine.api_payload import (
    build_link_rationales_payload,
    build_spine_payload,
)
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE_A = FIXTURES / "spine_index_a.json"
PAYLOAD_A = FIXTURES / "spine_api_payload_a.json"
DESIGN_SAMPLE = FIXTURES / "spine_design_sample.json"


def _count_causes_bridge(edges: list[dict]) -> int:
    return sum(1 for e in edges if e.get("edge_kind", "CAUSES") in ("CAUSES", "BRIDGE"))


def test_spine_index_a_payload_has_spines_and_selected_id():
    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    exp = json.loads(PAYLOAD_A.read_text(encoding="utf-8"))["expected"]
    spine = build_spine_payload(data["nodes"], data["edges"])
    assert len(spine["spines"]) >= exp["min_spines"]
    assert spine["selected_spine_id"]
    assert spine["selected_spine_id"] == spine["spines"][0]["spine_id"]
    assert set(spine.keys()) == set(exp["spine_block_keys"])
    assert spine["filters"] == exp["filters"]


def test_single_edge_empty_spine_payload():
    nodes = [
        GraphNode(id="a", subject="A", state_change="", timestamp=None, trigger_event=None),
        GraphNode(id="b", subject="B", state_change="", timestamp=None, trigger_event=None),
    ]
    edges = [GraphEdge(source_id="a", target_id="b", probability=1.0, latency=None)]
    spine = build_spine_payload(nodes, edges)
    assert spine["spines"] == []
    assert spine["selected_spine_id"] == ""


def test_link_rationales_count_matches_edges():
    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    rationales = build_link_rationales_payload(data["nodes"], data["edges"])
    assert len(rationales) == _count_causes_bridge(data["edges"])
    for item in rationales:
        assert item["link_sentence"]
        assert item["edge_kind"] in ("CAUSES", "BRIDGE")


def test_payload_keys_match_design_contract_sample():
    sample = json.loads(DESIGN_SAMPLE.read_text(encoding="utf-8"))
    contract = sample["contract_sample"]
    exp = json.loads(PAYLOAD_A.read_text(encoding="utf-8"))["expected"]

    data = json.loads(FIXTURE_A.read_text(encoding="utf-8"))
    spine = build_spine_payload(data["nodes"], data["edges"])
    rationales = build_link_rationales_payload(data["nodes"], data["edges"])

    assert set(spine.keys()) == set(contract["spine"].keys())
    assert spine["filters"] == contract["spine"]["filters"]
    if spine["spines"]:
        assert set(spine["spines"][0].keys()) == set(contract["spine"]["spines"][0].keys())
    assert set(rationales[0].keys()) == set(exp["link_rationale_keys"])
    assert set(rationales[0].keys()) == set(contract["link_rationales"][0].keys())


def test_pipeline_batch_result_includes_spine_blocks():
    import deconstructor.web.pipeline_batch as pb

    source = Path(pb.__file__).read_text(encoding="utf-8")
    assert "build_spine_payload" in source
    assert '"spine"' in source
    assert '"link_rationales"' in source
