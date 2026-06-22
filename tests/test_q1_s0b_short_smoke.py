"""μ-Q1-E2E-03 — S0-B short smoke checklist (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.q1_s0b_short_smoke_e2e import (
    REQUIRED_CHECKLIST_KEYS,
    V5_BASELINE_PASS2_SOURCE_COUNT,
    build_q1_checklist,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "q1_s0b_short_smoke_sample.json"


def test_q1_e2e_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["scenario"] == "S0-B-short-Q1-smoke"
    assert data["exit_code"] == 0
    cl = data["checklist"]
    assert REQUIRED_CHECKLIST_KEYS <= set(cl)
    assert cl["Phase-R_ok"] is True
    assert cl["pipeline_ok"] is True


def test_build_q1_checklist_from_minimal_state():
    state = {
        "completed_facts": [],
        "verified_edges_pass1": [],
        "pass2_gap_nodes": [{"id": "g1"}],
        "dreamer_log": ["[DREAM-S2-6] pass2_source_count=0 pass2_gap_count=1"],
        "promoted_facts": [],
        "dropped_hypotheses": [],
        "verified_edges": [],
        "partial_run": False,
    }
    skeleton = {"gap_count": 1, "weak_count": 0}
    cl = build_q1_checklist(
        read_ok=True,
        state=state,
        skeleton=skeleton,
        fc_mode="corpus",
        elapsed_sec=1.0,
    )
    assert cl["pass2_gap_count"] == 1
    assert cl["fc_mode"] == "corpus"
    assert cl["v5_baseline_pass2_source_count"] == V5_BASELINE_PASS2_SOURCE_COUNT


def test_q1_e2e_v5_baseline_constant():
    assert V5_BASELINE_PASS2_SOURCE_COUNT == 5
