"""μ-REG-B1-smoke — short Branch-1 regression (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "branch1_regression_smoke.py"
SAMPLE = ROOT / "tests" / "fixtures" / "branch1_regression_smoke_sample.json"
SPEC = ROOT / "docs" / "design" / "BRANCH-1-spec.md"


def test_smoke_script_exists_and_documents_mu():
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    assert "μ-REG-B1-smoke" in text
    assert "run_batch" in text
    assert "LINK_DISABLE_NEO4J_AUTO_START" in text
    assert "branch1_regression" in text


def test_smoke_spec_section():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "REG-B1-smoke" in body or "μ-REG-B1-smoke" in body


def test_smoke_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["scenario"] == "REG-B1-smoke"
    assert data["mu_id"] == "μ-REG-B1-smoke"
    ck = data["checklist"]
    assert ck["Phase-R_ok"] is True
    assert ck["pipeline_ok"] is True
    assert "fc_mode" in ck
    assert "elapsed_sec" in ck
