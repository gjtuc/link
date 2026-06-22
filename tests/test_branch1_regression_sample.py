"""μ-REG-B1ω — Branch-1 regression snapshot schema (offline)."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "branch1_regression_sample.json"

REQUIRED_TOP_KEYS = {
    "timestamp",
    "phase_r_exit",
    "branch1_full_exit",
    "duration_sec",
    "q1_note",
    "s0b",
    "s0c",
    "branch_state",
    "delta_vs_prior",
    "prior_branch1",
}

REQUIRED_S0B_KEYS = {"pipeline_ok", "gap_count", "weak_count", "fc_mode"}
REQUIRED_S0C_KEYS = {
    "pipeline_ok",
    "bridge_count",
    "cross_doc_label",
    "merge_mode",
}
REQUIRED_BRANCH_STATE_KEYS = {"branch_1_complete", "branch_2_unlocked"}


def test_branch1_regression_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert REQUIRED_TOP_KEYS <= set(data)
    assert data["phase_r_exit"] == 0
    assert data["branch1_full_exit"] == 0
    assert data["q1_note"] == "post Q1 2-pass"

    s0b = data["s0b"]
    assert REQUIRED_S0B_KEYS <= set(s0b)
    assert s0b["gap_count"] == 16
    assert s0b["weak_count"] == 2
    assert s0b["fc_mode"] == "corpus"

    s0c = data["s0c"]
    assert REQUIRED_S0C_KEYS <= set(s0c)
    assert s0c["bridge_count"] == 1
    assert s0c["merge_mode"] == "batch_corpus"
    assert "교차" in s0c["cross_doc_label"]

    bs = data["branch_state"]
    assert REQUIRED_BRANCH_STATE_KEYS <= set(bs)
    assert bs["branch_1_complete"] is True
    assert bs["branch_2_unlocked"] is False

    delta = data["delta_vs_prior"]["s0b"]
    assert delta["gap_count"]["prior"] == 20
    assert delta["gap_count"]["current"] == 16
    assert delta["weak_count"]["prior"] == 3
    assert delta["weak_count"]["current"] == 2
