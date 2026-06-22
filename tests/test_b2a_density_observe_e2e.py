"""μ-B2a-01 — density observe E2E script (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "b2a_density_observe_e2e.py"
SPEC = ROOT / "docs" / "design" / "BRANCH-2a-spec.md"
SAMPLE = ROOT / "tests" / "fixtures" / "b2a_density_observe_sample.json"
SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
LONG = ROOT / "tests" / "fixtures" / "s0b_draft_long.txt"


def test_b2a_script_exists_and_documents_mu():
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    assert "μ-B2a-01" in text
    assert "median_completed_facts" in text
    assert "b2a-density-observe" in text
    assert "log_capability_run" in text
    assert "b2a_density" in text
    assert "skip-phase-r" in text or "skip_phase_r" in text


def test_b2a_fixture_paths():
    assert SHORT.is_file()
    assert LONG.is_file()


def test_b2a_spec_documents_mu_b2a_01():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-B2a-01" in body
    assert "b2a_density_observe_e2e.py" in body


def test_b2a_density_observe_sample_shape():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-B2a-01"
    assert data["pipeline_ok"] is True
    assert "median_completed_facts" in data["deconstruct_batch"]
    assert data["ac_dec_02_median_target"] == 5
    assert isinstance(data["ac_dec_02_meets_should"], bool)
