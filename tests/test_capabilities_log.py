"""μ-Q2-05 — capability run log (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.log_capability_run import log_capability_run

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "capability_run_sample.json"

REQUIRED_RUN_KEYS = {"timestamp", "id", "script", "exit_code", "human_line"}


def test_capability_run_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_RUN_KEYS <= set(data)
    assert data["exit_code"] == 0
    assert data["id"] == "cap-s0b-draft"


def test_log_capability_run_writes(tmp_path):
    out = log_capability_run(
        "cap-s0b-draft",
        "s0b_e2e_run.py",
        0,
        human_line="test line",
        root=tmp_path,
    )
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert REQUIRED_RUN_KEYS <= set(data)
    assert data["human_line"] == "test line"
