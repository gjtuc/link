"""μ-Q2-03 — GET /api/capabilities."""

from __future__ import annotations

import json
from pathlib import Path

from deconstructor.capabilities import build_capabilities
from deconstructor.capabilities.build import CAPABILITY_ITEM_KEYS

ROOT = Path(__file__).resolve().parents[1]
SERVER_PY = ROOT / "deconstructor" / "web" / "server.py"
SAMPLE = ROOT / "tests" / "fixtures" / "capabilities_sample.json"


def test_capabilities_payload_keys():
    data = build_capabilities(ROOT)
    assert "capabilities" in data
    assert data["summary"]["verified"] >= 1
    for cap in data["capabilities"]:
        assert CAPABILITY_ITEM_KEYS <= set(cap)


def test_api_capabilities_sample_matches_build_shape():
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    live = build_capabilities(ROOT)
    assert set(sample.keys()) == {"generated_at", "branch_state", "capabilities", "summary"}
    assert len(sample["capabilities"]) == len(live["capabilities"])
    assert any(c["id"] == "cap-s0b-draft" for c in sample["capabilities"])
    assert any(c["status"] == "unsupported" for c in sample["capabilities"])


def test_server_registers_api_capabilities_route():
    """Offline: server.py wires GET /api/capabilities (avoids cgi import on Py3.13)."""
    source = SERVER_PY.read_text(encoding="utf-8")
    assert 'path == "/api/capabilities"' in source
    assert "build_capabilities" in source
