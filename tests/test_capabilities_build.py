"""μ-Q2-02 — capabilities build (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.capabilities.build import CAPABILITY_ITEM_KEYS, build_capabilities
from deconstructor.capabilities.catalog import CATALOG_SEEDS

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "capabilities_sample.json"

REQUIRED_TOP_KEYS = {
    "generated_at",
    "branch_state",
    "capabilities",
    "summary",
}


def test_capabilities_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_TOP_KEYS <= set(data)
    assert data["branch_state"]["branch_1_complete"] is True
    assert data["branch_state"]["branch_2_unlocked"] is True
    assert any(c["id"] == "cap-branch2a-active" for c in data["capabilities"])
    for cap in data["capabilities"]:
        assert CAPABILITY_ITEM_KEYS <= set(cap)
        assert cap["status"] in {"verified", "untested", "unsupported"}
        assert cap["human_line"].strip()
        assert cap["source"].strip()


def test_build_capabilities_live_matches_schema():
    payload = build_capabilities()
    assert REQUIRED_TOP_KEYS <= set(payload)
    assert len(payload["capabilities"]) >= 6
    assert payload["summary"]["verified"] >= 6
    catalog_ids = {c["id"] for c in payload["capabilities"] if c["id"].startswith("cat-")}
    assert len(catalog_ids) >= 6


def test_catalog_seed_count():
    assert len(CATALOG_SEEDS) >= 6


def test_catalog_neo4j_off_evidence_mentions_r1_contract():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    neo = by_id["cat-neo4j-off"]
    assert "LINK_DISABLE" in neo["evidence"]
    assert "96" in neo["evidence"] or "R1" in neo["evidence"]
    assert "DB" in neo["human_line"] or "Neo4j" in neo["human_line"]


def test_catalog_scanned_pdf_not_true_scan_consistent():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    scanned = by_id["cat-scanned-pdf"]
    assert "not_true_scan" in scanned["evidence"] or "스캔" in scanned["human_line"]
    assert scanned["status"] == "untested"


def test_catalog_scanned_pdf_evidence_mentions_r2a_handwriting():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    scanned = by_id["cat-scanned-pdf"]
    assert "R2a" in scanned["evidence"] or "handwriting" in scanned["evidence"]
    assert "scan_no_text_layer" in scanned["evidence"] or "empty_extract" in scanned["evidence"]


def test_catalog_scanned_pdf_evidence_mentions_r2b_watson_crick():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    scanned = by_id["cat-scanned-pdf"]
    assert "R2b" in scanned["evidence"] or "watson" in scanned["evidence"].lower()
    assert "scan_ocr_noisy" in scanned["evidence"] or "6630" in scanned["evidence"]
    assert scanned["status"] == "untested"


def test_catalog_pdf_triple_evidence_has_probe():
    by_id = {c["id"]: c for c in CATALOG_SEEDS}
    triple = by_id["cat-pdf-triple"]
    assert "3 source_file" in triple["evidence"]
    assert triple["status"] == "untested"
