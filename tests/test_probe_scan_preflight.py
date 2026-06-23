"""μ-PROBE-SCAN-R2a-0 — handwriting scan PDF preflight (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.web.extract import _read_pdf_pages

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "probe_scan_preflight_sample.json"
PDF = FIXTURES / "probe_scan_handwriting.pdf"

REQUIRED_KEYS = {
    "mu_id",
    "fixture",
    "pypdf_extract_chars",
    "page_count",
    "pdf_class",
}


def test_probe_scan_preflight_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS <= set(data)
    assert data["mu_id"] == "μ-PROBE-SCAN-R2a"
    assert data["pdf_class"] == "scan_no_text_layer"
    assert data["pypdf_extract_chars"] == 0
    assert data["page_count"] == 1


def test_probe_scan_handwriting_pdf_zero_chars_one_page():
    assert PDF.is_file(), f"missing fixture {PDF.name}"
    pages = _read_pdf_pages(PDF.read_bytes())
    assert len(pages) == 1
    chars = sum(len(p) for p in pages)
    assert chars == 0


def test_probe_spec_documents_scan_r2a():
    spec = Path(__file__).resolve().parents[1] / "docs" / "design" / "CAPABILITY-PROBE-spec.md"
    body = spec.read_text(encoding="utf-8")
    assert "μ-PROBE-SCAN-R2a" in body
    assert "scan_no_text_layer" in body
    assert "handwriting" in body
