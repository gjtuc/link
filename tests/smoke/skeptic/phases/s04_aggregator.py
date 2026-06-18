"""Skeptic smoke phase 4 — aggregator micro-steps."""

from __future__ import annotations

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.aggregator import aggregate_verdict
from deconstructor.skeptic.schemas import CausalHypothesis
from tests.conftest import GRID_OFF, WEATHER_HOT
from tests.smoke.harness import StepRunner


def phase_aggregator_micro(run: StepRunner) -> None:
    run.section("4 Aggregator micro-steps")
    engine = SkepticEngine()
    v = engine.evaluate_hypothesis(
        CausalHypothesis(source_fact_id="f1", target_fact_id="f3"),
        {"f1": GRID_OFF, "f3": WEATHER_HOT},
    )
    cls, accepted, trace = aggregate_verdict(v.rule_results)
    run.ok("weather rejected", not accepted)
    run.ok("classified correlation", cls.value == "correlation")
    run.ok("agg trace non-empty", len(trace) >= 1)
    run.ok("agg step A1 or A2", trace[0].step_id in ("A1", "A2", "A3"))
