"""μ-CAT-03 — capabilities status policy (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.capabilities.build import VALID_STATUSES, build_capabilities
from deconstructor.capabilities.catalog import CATALOG_SEEDS

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "design" / "Q2-CAPABILITIES-spec.md"
PROBE_SPEC = ROOT / "docs" / "design" / "CAPABILITY-PROBE-spec.md"
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "capabilities_policy_sample.json"

CATALOG_IDS = {c["id"] for c in CATALOG_SEEDS}


def test_capabilities_policy_spec_has_status_policy_section():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-CAT-01" in body
    assert "## Status policy" in body
    assert "probe 1회만으로 `verified`" in body or "probe 1회만으로 verified" in body
    assert "감독 승인" in body
    assert "cat-scanned-pdf" in body
    assert "untested` 유지" in body or "untested 유지" in body


def test_capabilities_policy_spec_has_evidence_matrix():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-CAT-02" in body
    assert "Evidence matrix" in body
    assert "μ-PROBE-SCAN-R2a" in body
    assert "μ-PROBE-SCAN-R2b" in body
    assert "μ-PROBE-SCAN-ω" in body


def test_capability_probe_spec_links_evidence_matrix():
    body = PROBE_SPEC.read_text(encoding="utf-8")
    assert "μ-CAT-02" in body
    assert "Q2-CAPABILITIES-spec.md" in body


def test_capabilities_policy_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-CAT-03"
    assert set(data["policy_statuses"]) == VALID_STATUSES
    assert data["forbidden"] == "probe_single_run_to_verified"
    scanned = data["cat_scanned_pdf"]
    assert scanned["status"] == "untested"
    assert "conflicting" in scanned["reason"]


def test_build_capabilities_catalog_respects_policy():
    payload = build_capabilities()
    by_id = {c["id"]: c for c in payload["capabilities"]}
    for seed in CATALOG_SEEDS:
        live = by_id[seed["id"]]
        assert live["status"] == seed["status"]
        assert live["status"] in {"untested", "unsupported"}
    scanned = by_id["cat-scanned-pdf"]
    assert scanned["status"] == "untested"
    assert "R2a" in scanned["evidence"] or "handwriting" in scanned["evidence"]
    assert "R2b" in scanned["evidence"] or "watson" in scanned["evidence"].lower()


def test_build_capabilities_verified_from_e2e_not_catalog():
    payload = build_capabilities()
    verified = [c for c in payload["capabilities"] if c["status"] == "verified"]
    assert len(verified) >= 6
    assert all(not c["id"].startswith("cat-") for c in verified)
