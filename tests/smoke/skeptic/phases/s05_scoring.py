"""Skeptic smoke phase 5 — scoring."""

from __future__ import annotations

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.schemas import CausalHypothesis
from deconstructor.skeptic.scoring import compute_latency_ms, compute_probability
from tests.conftest import GRID_OFF, MOTOR_STOP
from tests.smoke.harness import StepRunner


def phase_scoring(run: StepRunner) -> None:
    run.section("5 Scoring")
    engine = SkepticEngine()
    v = engine.evaluate_hypothesis(
        CausalHypothesis(source_fact_id="f1", target_fact_id="f2"),
        {"f1": GRID_OFF, "f2": MOTOR_STOP},
    )
    assert v.verified_edge
    run.ok("probability > 0", v.verified_edge.probability > 0)
    run.ok("latency 120s", v.verified_edge.latency == 120_000)
    run.ok(
        "compute_latency match",
        compute_latency_ms(GRID_OFF, MOTOR_STOP) == 120_000,
    )
    run.ok(
        "compute_probability match",
        compute_probability(v.rule_results) == v.verified_edge.probability,
    )
