"""μ-POST-Q2-0d — stage0 reaudit post-Q2 sample schema (offline)."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "stage0_reaudit_post_q2_sample.json"

REQUIRED_TOP_KEYS = {
    "timestamp",
    "branch_state",
    "phase_r_regression_exit",
    "pytest",
    "pytest_q1",
    "pytest_q2",
    "q2_capabilities",
    "record_phase_a",
    "closure_spec_rows",
    "mismatches",
}

REQUIRED_Q2_CAP_KEYS = {"verified", "untested", "unsupported", "total"}


def test_post_q2_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_TOP_KEYS <= set(data)
    assert data["mismatches"] == []
    assert data["phase_r_regression_exit"] == 0
    assert data["branch_state"]["branch_1_complete"] is True
    assert data["branch_state"]["branch_2_unlocked"] is True
    assert REQUIRED_Q2_CAP_KEYS <= set(data["q2_capabilities"])
    assert data["q2_capabilities"]["total"] >= 10
    assert data["q2_capabilities"]["verified"] >= 1
    assert data["pytest_q1"]["exit_code"] == 0
    assert data["pytest_q2"]["exit_code"] == 0
