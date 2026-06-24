"""μ-STAGE0-ω — AC-DEC-02 B2a observation links (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "stage0_ac_dec02_observation_sample.json"
STAGE0_3 = ROOT / "docs" / "design" / "STAGE-0-3-acceptance-criteria.md"
STAGE0_4 = ROOT / "docs" / "design" / "STAGE-0-4-current-vs-target.md"
RECORD = ROOT / "docs" / "design" / "B2a-DENSITY-OBSERVE-RECORD.md"
ROADMAP = ROOT / "docs" / "design" / "STAGE-0-CLOSURE-ROADMAP.md"
PROBE_SPEC = ROOT / "docs" / "design" / "CAPABILITY-PROBE-spec.md"


def test_stage0_ac_dec02_observation_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-STAGE0-ω"
    assert data["ac_id"] == "AC-DEC-02"
    assert data["level"] == "SHOULD"
    assert data["must_promotion_forbidden"] is True
    obs = data["observations"]
    assert len(obs) == 2
    assert obs[0]["median_completed_facts"] == 5.5
    assert obs[0]["commit"] == "b268c08"
    assert obs[1]["median_completed_facts"] == 12.0
    assert obs[1]["commit"] == "51c3afa"
    assert all(o["meets_should"] for o in obs)
    assert "μ-PROBE-SCAN-R2a" in data["scan_ingest"]["probes"]


def test_stage0_3_ac_dec02_links_b2a_observations():
    body = STAGE0_3.read_text(encoding="utf-8")
    assert "AC-DEC-02" in body
    assert "B2a-DENSITY-OBSERVE-RECORD.md" in body
    assert "5.5" in body
    assert "b268c08" in body
    assert "12.0" in body or "12" in body
    assert "51c3afa" in body
    assert "MUST 승격 금지" in body


def test_stage0_4_g_dec_dens_links_b2a_observations():
    body = STAGE0_4.read_text(encoding="utf-8")
    assert "G-DEC-DENS" in body
    assert "b268c08" in body
    assert "51c3afa" in body
    assert "CAPABILITY-PROBE-spec.md" in body
    assert "μ-PROBE-SCAN-R2a" in body


def test_roadmap_documents_stage0_wave3():
    body = ROADMAP.read_text(encoding="utf-8")
    assert "μ-STAGE0-ω" in body
    assert "Branch-0" in body and "MUST" in body


def test_b2a_record_matches_sample_medians():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    body = RECORD.read_text(encoding="utf-8")
    assert str(data["observations"][0]["median_completed_facts"]) in body
    assert "12.0" in body or "12" in body


def test_probe_spec_referenced_for_scan_ingest():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    body = PROBE_SPEC.read_text(encoding="utf-8")
    assert PROBE_SPEC.is_file()
    for probe in data["scan_ingest"]["probes"]:
        assert probe in body
