"""μ-PROBE-SCAN-ω — born-digital scan attempt sample (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.capabilities.catalog import CATALOG_SEEDS

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "capability_scan_attempt_sample.json"
SPEC = Path(__file__).resolve().parents[1] / "docs" / "design" / "CAPABILITY-PROBE-spec.md"

REQUIRED_KEYS = {
    "mu_id",
    "scenario",
    "cat_id",
    "catalog_unchanged",
    "pdf_class",
    "phase_r_ok",
    "pipeline_ok",
    "failed_step",
    "failure_class",
    "exit_code",
    "elapsed_sec",
    "log_ref",
}


def test_capability_scan_attempt_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS <= set(data)
    assert data["mu_id"] == "μ-PROBE-SCAN-ω"
    assert data["pdf_class"] == "born-digital"
    assert data["failure_class"] == "gemini_503"
    assert data["catalog_unchanged"] is True
    assert data["exit_code"] == 2


def test_probe_spec_documents_scan_omega():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-PROBE-SCAN-ω" in body
    assert "born-digital" in body
    assert "3059.7" in body or "3059" in body


def test_catalog_scanned_pdf_not_true_scan_unchanged():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    scanned = by_id["cat-scanned-pdf"]
    assert "not_true_scan" in scanned["evidence"]
