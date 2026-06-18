"""Skeptic smoke phase 1 — rule registry."""

from __future__ import annotations

from deconstructor.skeptic.rules import build_rule_registry
from tests.smoke.harness import StepRunner


def phase_registry(run: StepRunner) -> None:
    run.section("1 Rule registry")
    reg = build_rule_registry()
    run.ok("11 rules registered", len(reg) == 11)
    ids = [e.rule.rule_id for e in reg]
    run.ok("R01 first", ids[0] == "R01_NO_SELF_LOOP")
    run.ok(
        "R08 narrative before temporal",
        ids.index("R08_NARRATIVE_LEAK") < ids.index("R03_TEMPORAL_ORDER"),
    )
    run.ok(
        "R11 before structural",
        ids.index("R11_POST_HOC_ZERO_LAG") < ids.index("R05_COMMON_CAUSE_PATTERN"),
    )
