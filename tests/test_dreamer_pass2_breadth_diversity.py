"""μ-V5 — 2-pass pass2 Flash breadth diversity (offline + optional live)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_dreamer_breadth_diversity import DIV03_THRESHOLDS, _assert_div03_thresholds

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "dreamer_breadth"

REQUIRED_SUMMARY_KEYS = frozenset(
    {
        "mode",
        "fixture",
        "runs",
        "pass1_edge_count",
        "pass2_gap_count",
        "pass2_source_count",
        "averages",
        "div03_pass",
    }
)


def _load_pass2_summary(fixture: str) -> dict:
    summaries = sorted(LOG_DIR.glob(f"pass2-{fixture}-*-summary.json"))
    if summaries:
        return json.loads(summaries[-1].read_text(encoding="utf-8"))
    sample = FIXTURES_DIR / f"dreamer_breadth_pass2_{fixture}_summary_sample.json"
    if sample.is_file():
        return json.loads(sample.read_text(encoding="utf-8"))
    raise pytest.skip(
        f"no pass2 {fixture} summary — run dreamer_pass2_breadth_probe.py --fixture {fixture} --runs 3"
    )


def test_v5_pass2_summary_schema_s0b_sample():
    data = json.loads(
        (FIXTURES_DIR / "dreamer_breadth_pass2_s0b_summary_sample.json").read_text(encoding="utf-8")
    )
    assert data["mode"] == "2pass_pass2"
    assert data["fixture"] == "s0b"
    assert REQUIRED_SUMMARY_KEYS <= set(data)
    assert "exact_duplicate_rate" in data["averages"]
    assert data["div03_pass"] is True


def test_v5_div03_thresholds_shared_with_div03():
    assert DIV03_THRESHOLDS["exact_duplicate_rate_max"] == 0.10
    assert DIV03_THRESHOLDS["unique_subject_ratio_min"] == 0.70
    assert DIV03_THRESHOLDS["mechanism_similarity_mean_max"] == 0.15


def test_v5_pass2_sample_meets_div03_thresholds():
    data = _load_pass2_summary("s0b")
    _assert_div03_thresholds(data)


@pytest.mark.live
def test_v5_live_pass2_s0b_meets_thresholds():
    pytest.importorskip("langchain_google_genai")
    data = _load_pass2_summary("s0b")
    assert data.get("mode") == "2pass_pass2"
    _assert_div03_thresholds(data)


@pytest.mark.live
def test_v5_live_pass2_s0a_meets_thresholds():
    pytest.importorskip("langchain_google_genai")
    data = _load_pass2_summary("s0a")
    assert data.get("mode") == "2pass_pass2"
    _assert_div03_thresholds(data)
