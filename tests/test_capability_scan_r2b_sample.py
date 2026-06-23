"""μ-PROBE-SCAN-R2b — watson-crick OCR scan live sample (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.capabilities.catalog import CATALOG_SEEDS

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "capability_scan_r2b_sample.json"
SPEC = Path(__file__).resolve().parents[1] / "docs" / "design" / "CAPABILITY-PROBE-spec.md"

REQUIRED_KEYS = {
    "mu_id",
    "scenario",
    "cat_id",
    "catalog_unchanged",
    "file",
    "pdf_class",
    "pypdf_extract_chars",
    "page_count",
    "phase_r_ok",
    "pipeline_ok",
    "failure_class",
    "exit_code",
    "elapsed_sec",
    "log_ref",
}


def test_capability_scan_r2b_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS <= set(data)
    assert data["mu_id"] == "μ-PROBE-SCAN-R2b"
    assert data["pdf_class"] == "scan_ocr_noisy"
    assert data["pypdf_extract_chars"] > 1000
    assert data["page_count"] == 2
    assert data["catalog_unchanged"] is True


def test_probe_spec_documents_scan_r2b_live():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-PROBE-SCAN-R2b" in body
    assert "molecularstructureofDNAswatsoncrick" in body or "watson-crick" in body


def test_catalog_scanned_pdf_evidence_mentions_r2b():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    scanned = by_id["cat-scanned-pdf"]
    assert "R2b" in scanned["evidence"] or "watson" in scanned["evidence"].lower()
    assert scanned["status"] == "untested"
