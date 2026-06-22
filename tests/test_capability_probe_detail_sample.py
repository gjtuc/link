"""μ-PROBE — capability probe detail schema (offline)."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "capability_probe_detail_sample.json"

REQUIRED_KEYS = {
    "scenario",
    "cat_id",
    "files",
    "neo4j_available",
    "pipeline_ok",
    "elapsed_sec",
}


def test_capability_probe_detail_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS <= set(data)
    assert data["cat_id"].startswith("cat-")
