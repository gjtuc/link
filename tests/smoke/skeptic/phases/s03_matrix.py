"""Skeptic smoke phase 3 — per-rule scenario matrix."""

from __future__ import annotations

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.fixtures.catalog import PAIR_SCENARIOS
from deconstructor.skeptic.schemas import CausalHypothesis, RuleOutcome
from tests.smoke.harness import StepRunner


def phase_per_rule_matrix(run: StepRunner) -> None:
    run.section("3 Per-rule scenario matrix")
    engine = SkepticEngine()
    for sc in PAIR_SCENARIOS:
        hyp = CausalHypothesis(
            source_fact_id=sc.source.id,
            target_fact_id=sc.target.id,
            proposed_mechanism=sc.mechanism,
        )
        facts = {sc.source.id: sc.source, sc.target.id: sc.target}
        v = engine.evaluate_hypothesis(hyp, facts)
        run.ok(
            sc.label,
            v.accepted == sc.expect_accepted,
            f"accepted={v.accepted}",
        )
        if sc.expect_fail_rule:
            failed = [r.rule_id for r in v.rule_results if r.outcome == RuleOutcome.FAIL]
            run.ok(
                f"{sc.label} fail rule",
                sc.expect_fail_rule in failed,
                f"failed={failed}",
            )
