"""μ-MAINT-ω — Branch-0 health check (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "branch0_health_check.py"
SPEC = ROOT / "docs" / "design" / "BRANCH-0-MAINTENANCE-spec.md"
PROCESS = ROOT / "docs" / "design" / "PROCESS.md"
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "branch0_health_sample.json"


def test_branch0_health_script_exists_and_documents_mu():
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    assert "μ-MAINT-02" in text
    assert "branch0_health" in text
    assert "BRANCH-0-MAINTENANCE-spec.md" in text
    assert "stage0_reaudit_baseline" in text
    assert "phase_r_regression" in text
    assert "branch1_full_e2e" in text


def test_branch0_maintenance_spec_links_manifest():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-MAINT-R" in body
    assert "μ-MAINT-ω" in body
    assert "ingest_manifest.py" in body
    assert "INGEST_TOUCH_PATHS" in body
    assert "branch0_health_check.py" in body


def test_process_links_branch0_maintenance_spec():
    body = PROCESS.read_text(encoding="utf-8")
    assert "BRANCH-0-MAINTENANCE-spec.md" in body


def test_branch0_health_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-MAINT-02"
    assert isinstance(data["ok"], bool)
    assert isinstance(data["steps"], list)
    assert data["mismatches"] == []
    assert len(data["steps"]) >= 3
