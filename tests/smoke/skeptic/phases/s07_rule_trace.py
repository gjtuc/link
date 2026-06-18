"""Skeptic smoke phase 7 — full rule trace."""

from __future__ import annotations

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.rules import RULE_BY_ID
from deconstructor.skeptic.schemas import CausalHypothesis, RuleContext
from tests.conftest import GRID_OFF, MOTOR_STOP
from tests.smoke.harness import StepRunner


def phase_rule_trace_count(run: StepRunner) -> None:
    run.section("7 Full rule trace per hypothesis")
    engine = SkepticEngine()
    c = RuleContext(
        source=GRID_OFF,
        target=MOTOR_STOP,
        hypothesis=CausalHypothesis(source_fact_id="f1", target_fact_id="f2"),
    )
    results = engine.run_rules(c)
    run.ok("11 rule results", len(results) == 11)
    run.ok("all have rule_id", all(r.rule_id in RULE_BY_ID for r in results))
