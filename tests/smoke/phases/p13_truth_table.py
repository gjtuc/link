"""Phase 13 — Skeptic ABSTAIN truth table."""

from __future__ import annotations

from deconstructor.skeptic.truth_table import (
    build_abstain_combination_table,
    build_core_truth_table,
    verify_truth_table,
)
from tests.smoke.harness import StepRunner


def phase_13_truth_table(run: StepRunner) -> None:
    run.section("13a core aggregator paths")

    core_errors = verify_truth_table(build_core_truth_table())
    run.check("core table clean", core_errors == [], str(core_errors))

    run.section("13b abstain combination table")

    abstain_rows = build_abstain_combination_table()
    run.check("8 rows", len(abstain_rows) == 8)
    abstain_errors = verify_truth_table(abstain_rows)
    run.check("abstain table clean", abstain_errors == [], str(abstain_errors))
