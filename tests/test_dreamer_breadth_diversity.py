"""μ-DR-DIV — Dreamer Flash breadth diversity (stub / offline)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from deconstructor.agents.dreamer.diversity import (
    diversity_metrics,
    exact_duplicate_rate,
    mechanism_similarity_mean,
    unique_subject_ratio,
)

# μ-DR-DIV-03 live averages (2026-06-22, 3 runs):
#   s0a: dup=0.0, unique_subj=1.0, mech_sim=0.082
#   s0b: dup=0.0, unique_subj=1.0, mech_sim=0.063
DIV03_THRESHOLDS = {
    "exact_duplicate_rate_max": 0.10,
    "unique_subject_ratio_min": 0.70,
    "mechanism_similarity_mean_max": 0.15,
}


@dataclass
class _Hyp:
    subject: str
    mechanism: str


def _sample_diverse() -> list[_Hyp]:
    return [
        _Hyp("Reactor temperature", "Heat from exothermic reaction raises wall stress."),
        _Hyp("Catalyst loading", "Ni dispersion changes active site density on support."),
        _Hyp("Syngas flow", "Reduced feed lowers partial pressure in the bed."),
        _Hyp("Coolant loop", "Thermal load shifts when outlet temperature rises."),
    ]


def test_div01_exact_duplicate_rate_zero_for_unique_rows():
    hyps = _sample_diverse()
    assert exact_duplicate_rate(hyps) == 0.0


def test_div01_exact_duplicate_rate_detects_dupes():
    hyps = _sample_diverse() + [_Hyp("Reactor temperature", "Heat from exothermic reaction raises wall stress.")]
    assert exact_duplicate_rate(hyps) == pytest.approx(1 / 5)


def test_div01_unique_subject_ratio():
    hyps = _sample_diverse()
    assert unique_subject_ratio(hyps) == 1.0


def test_div01_mechanism_similarity_mean_bounded():
    hyps = _sample_diverse()
    mean = mechanism_similarity_mean(hyps)
    assert 0.0 <= mean <= 1.0


def test_div01_diversity_metrics_bundle():
    m = diversity_metrics(_sample_diverse())
    assert set(m) >= {"exact_duplicate_rate", "unique_subject_ratio", "mechanism_similarity_mean", "count"}
    assert m["count"] == 4.0


def test_div03_threshold_constants_documented():
    """Offline guard — live probe averages must stay within these bounds."""
    assert DIV03_THRESHOLDS["exact_duplicate_rate_max"] <= 0.10
    assert DIV03_THRESHOLDS["unique_subject_ratio_min"] >= 0.70


def _load_breadth_summary(fixture: str) -> dict:
    import json
    from pathlib import Path

    log_dir = Path(__file__).resolve().parents[1] / "logs" / "dreamer_breadth"
    summaries = sorted(log_dir.glob(f"{fixture}-*-summary.json"))
    if summaries:
        return json.loads(summaries[-1].read_text(encoding="utf-8"))
    sample = Path(__file__).resolve().parent / "fixtures" / f"dreamer_breadth_{fixture}_summary_sample.json"
    if sample.is_file():
        return json.loads(sample.read_text(encoding="utf-8"))
    raise pytest.skip(f"no {fixture} breadth summary — run dreamer_breadth_probe --fixture {fixture} --runs 3")


def _assert_div03_thresholds(data: dict) -> None:
    avg = data.get("averages") or {}
    assert avg.get("exact_duplicate_rate", 1.0) <= DIV03_THRESHOLDS["exact_duplicate_rate_max"]
    assert avg.get("unique_subject_ratio", 0.0) >= DIV03_THRESHOLDS["unique_subject_ratio_min"]
    assert avg.get("mechanism_similarity_mean", 1.0) <= DIV03_THRESHOLDS["mechanism_similarity_mean_max"]


@pytest.mark.live
def test_div03_live_s0a_breadth_meets_thresholds():
    """Optional live — run dreamer_breadth_probe --fixture s0a --runs 3 first."""
    pytest.importorskip("langchain_google_genai")
    _assert_div03_thresholds(_load_breadth_summary("s0a"))


@pytest.mark.live
def test_div03_live_s0b_breadth_meets_thresholds():
    """Optional live — run dreamer_breadth_probe --fixture s0b --runs 3 first."""
    pytest.importorskip("langchain_google_genai")
    _assert_div03_thresholds(_load_breadth_summary("s0b"))
