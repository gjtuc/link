"""μ-B2a-02 — S0-A PDF density observe E2E script (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "b2a_density_s0a_observe_e2e.py"
SPEC = ROOT / "docs" / "design" / "BRANCH-2a-spec.md"
SAMPLE = ROOT / "tests" / "fixtures" / "b2a_density_s0a_observe_sample.json"
S0A = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"


def test_b2a_s0a_script_exists_and_documents_mu():
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    assert "μ-B2a-02" in text
    assert "s0a_paper.pdf" in text
    assert "median_completed_facts" in text
    assert "b2a-density-s0a-observe" in text
    assert "log_capability_run" in text


def test_b2a_s0a_fixture_exists():
    assert S0A.is_file()


def test_b2a_spec_documents_mu_b2a_02():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-B2a-02" in body
    assert "b2a_density_s0a_observe_e2e.py" in body


def test_b2a_density_s0a_observe_sample_shape():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-B2a-02"
    assert data["fixture"] == "s0a_paper.pdf"
    assert "median_completed_facts" in data["deconstruct_batch"]
    assert data["ac_dec_02_median_target"] == 5
    assert isinstance(data["ac_dec_02_meets_should"], bool)
