"""
μ-SPINE-00 — SPINE design sample (offline contract gate).

Validates BRANCH-SPINE-spec + STAGE-0-SPINE-1~3 docs and spine_design_sample.json.
No pipeline / UI implementation — design freeze only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "spine_design_sample.json"
SPEC = ROOT / "docs" / "design" / "BRANCH-SPINE-spec.md"
PHILOSOPHY = ROOT / "docs" / "design" / "STAGE-0-SPINE-philosophy.md"
SCENARIOS = ROOT / "docs" / "design" / "STAGE-0-SPINE-2-scenarios.md"
ACCEPTANCE = ROOT / "docs" / "design" / "STAGE-0-SPINE-3-acceptance.md"


def _load_sample() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_spine_design_sample_schema():
    data = _load_sample()
    assert data["mu_id"] == "μ-SPINE-00"
    assert data["branch"] == "Branch-SPINE"
    assert data["status"] == "unlocked"
    assert data["implementation_started"] is True
    assert data["unlock_fields"]["spine_design_complete"] is True
    assert data["unlock_fields"]["branch_spine_unlocked"] is True
    assert "μ-SPINE-01" in data["mu_ids_planned"]
    must = data["must_ac_bundle"]
    assert "C-SPINE-05" in must
    assert "C-SPINE-01" in must
    assert "C-SPINE-08" in must


def test_spine_contract_sample_shape():
    data = _load_sample()
    spine = data["contract_sample"]["spine"]
    assert len(spine["spines"]) >= 1
    rec = spine["spines"][0]
    for key in (
        "spine_id",
        "index",
        "label",
        "bridge_count",
        "node_ids",
        "edge_ids",
        "main_path_node_ids",
        "is_branched",
    ):
        assert key in rec
    assert spine["selected_spine_id"] == rec["spine_id"]
    filters = spine["filters"]
    assert filters["include_hypothesis"] is False
    assert filters["include_bridge"] is True

    rationales = data["contract_sample"]["link_rationales"]
    assert len(rationales) >= 2
    causes = [r for r in rationales if r["edge_kind"] == "CAUSES"]
    assert len(causes) >= 2
    for r in rationales:
        assert r["source_fact_id"] and r["target_fact_id"]
        assert "link_sentence" in r
        assert "link_mechanism" in r
        assert r["locale"] in ("ko", "en")


def test_branch_spine_spec_exists_with_required_sections():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-SPINE-00" in body
    assert "LinkRationale" in body
    assert "SpineRecord" in body
    assert "link_rationales" in body
    assert "branch_spine_unlocked" in body
    assert "## NON-GOALS" in body
    assert "μ-SPINE-01" in body


def test_spine_philosophy_scenarios_acceptance_linked():
    for path in (PHILOSOPHY, SCENARIOS, ACCEPTANCE):
        assert path.is_file()
    phil = PHILOSOPHY.read_text(encoding="utf-8")
    assert "§1f" in phil
    assert "S-SPINE-A" in phil
    scen = SCENARIOS.read_text(encoding="utf-8")
    assert "S-SPINE-A" in scen
    assert "S-SPINE-B" in scen
    ac = ACCEPTANCE.read_text(encoding="utf-8")
    assert "C-SPINE-05" in ac
    assert "spine_closure_a.json" in ac


def test_spine_design_sample_spec_refs_exist():
    data = _load_sample()
    for rel in data["related_specs"] + [data["spec_ref"]]:
        assert (ROOT / rel).is_file(), rel
