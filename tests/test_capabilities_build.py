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


def test_each_capability_has_human_line():
    for cap in build_capabilities()["capabilities"]:
        assert len(cap["human_line"]) >= 8
