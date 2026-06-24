"""μ-B2a-ω — Branch-2a 1차 관측 마감 (offline)."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "b2a_closure_sample.json"
SPEC = Path(__file__).resolve().parents[1] / "docs" / "design" / "BRANCH-2a-spec.md"
ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "design" / "STAGE-0-CLOSURE-ROADMAP.md"
HANDOFF = Path(__file__).resolve().parents[1] / "docs" / "design" / "SUPERVISOR-AI-HANDOFF.md"
RECORD = Path(__file__).resolve().parents[1] / "docs" / "design" / "B2a-DENSITY-OBSERVE-RECORD.md"

PAR_B2A_01 = FIXTURES / "b2a_density_observe_sample.json"
PAR_B2A_02 = FIXTURES / "b2a_density_s0a_observe_sample.json"


def test_b2a_closure_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-B2a-ω"
    assert data["closure"] == "1차 관측 마감"
    assert data["live_e2e_rerun"] is False
    assert data["branch_2b_locked"] is True
    obs = data["observations"]
    assert obs["mu_b2a_01"]["median_completed_facts"] == 5.5
    assert obs["mu_b2a_02"]["median_completed_facts"] == 12.0


def test_b2a_closure_sample_matches_density_fixtures():
    closure = json.loads(SAMPLE.read_text(encoding="utf-8"))
    b01 = json.loads(PAR_B2A_01.read_text(encoding="utf-8"))
    b02 = json.loads(PAR_B2A_02.read_text(encoding="utf-8"))
    assert closure["observations"]["mu_b2a_01"]["median_completed_facts"] == b01["deconstruct_batch"]["median_completed_facts"]
    assert closure["observations"]["mu_b2a_02"]["median_completed_facts"] == b02["deconstruct_batch"]["median_completed_facts"]


def test_branch2a_spec_documents_b2a_omega():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-B2a-ω" in body
    assert "1차 관측" in body or "마감" in body
    assert "5.5" in body
    assert "12.0" in body or "12" in body


def test_roadmap_branch2a_first_observation_closed():
    body = ROADMAP.read_text(encoding="utf-8")
    assert "μ-B2a-ω" in body or "1차 관측" in body
    assert "μ-B2a-03" in body
    assert "median=5.5" in body or "5.5" in body
    assert "median=12" in body or "12.0" in body


def test_handoff_documents_b2a_omega_complete():
    body = HANDOFF.read_text(encoding="utf-8")
    assert "μ-B2a-ω" in body or "B2a ω" in body or "1차 관측" in body


def test_b2a_record_documents_both_observations():
    body = RECORD.read_text(encoding="utf-8")
    assert "5.5" in body
    assert "12.0" in body or "12" in body
    assert "s0a_paper.pdf" in body
