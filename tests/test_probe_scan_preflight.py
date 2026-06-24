"""μ-PROBE-SCAN-R2a/R2b — scan PDF preflight (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.web.extract import _read_pdf_pages

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "probe_scan_preflight_sample.json"
PDF_R2A = FIXTURES / "probe_scan_handwriting.pdf"
PDF_R2B = FIXTURES / "probe_scan_watson_crick.pdf"

BLOCK_KEYS = {
    "mu_id",
    "fixture",
    "pypdf_extract_chars",
    "page_count",
    "pdf_class",
}


def test_probe_scan_preflight_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    for key in ("r2a", "r2b"):
        assert key in data
        assert BLOCK_KEYS <= set(data[key])


def test_probe_scan_preflight_sample_r2a():
    r2a = json.loads(SAMPLE.read_text(encoding="utf-8"))["r2a"]
    assert r2a["mu_id"] == "μ-PROBE-SCAN-R2a"
    assert r2a["pdf_class"] == "scan_no_text_layer"
    assert r2a["pypdf_extract_chars"] == 0
    assert r2a["page_count"] == 1


def test_probe_scan_preflight_sample_r2b():
    r2b = json.loads(SAMPLE.read_text(encoding="utf-8"))["r2b"]
    assert r2b["mu_id"] == "μ-PROBE-SCAN-R2b"
    assert r2b["pdf_class"] == "scan_ocr_noisy"
    assert r2b["pypdf_extract_chars"] > 1000
    assert r2b["page_count"] == 2


def test_probe_scan_handwriting_pdf_zero_chars_one_page():
    assert PDF_R2A.is_file(), f"missing fixture {PDF_R2A.name}"
    pages = _read_pdf_pages(PDF_R2A.read_bytes())
    assert len(pages) == 1
    chars = sum(len(p) for p in pages)
    assert chars == 0


def test_probe_scan_watson_crick_pdf_noisy_ocr_chars():
    assert PDF_R2B.is_file(), f"missing fixture {PDF_R2B.name}"
    pages = _read_pdf_pages(PDF_R2B.read_bytes())
    assert len(pages) == 2
    chars = sum(len(p) for p in pages)
    assert chars > 1000
    text = "".join(pages)
    assert "MOLECULAR" in text
    assert "suggecit" in text


def test_probe_spec_documents_scan_r2a():
    spec = Path(__file__).resolve().parents[1] / "docs" / "design" / "CAPABILITY-PROBE-spec.md"
    body = spec.read_text(encoding="utf-8")
    assert "μ-PROBE-SCAN-R2a" in body
    assert "scan_no_text_layer" in body
    assert "handwriting" in body


def test_probe_spec_documents_scan_r2b():
    spec = Path(__file__).resolve().parents[1] / "docs" / "design" / "CAPABILITY-PROBE-spec.md"
    body = spec.read_text(encoding="utf-8")
    assert "μ-PROBE-SCAN-R2b" in body
    assert "scan_ocr_noisy" in body
