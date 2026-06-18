"""Phase 6 — Multi-headline matrix."""

from __future__ import annotations

from deconstructor.dry_run.scenarios import HEADLINE_SCENARIOS
from deconstructor.pipeline_trace import run_pipeline_traced
from tests.smoke.constants import EXPECTED_NODE_SEQUENCE
from tests.smoke.harness import StepRunner


def phase_6_matrix(run: StepRunner) -> None:
    run.section("6 headline matrix")

    for scenario in HEADLINE_SCENARIOS:
        traced = run_pipeline_traced(scenario.headline, dry_run=True)
        st = traced.final_state
        run.check(
            f"{scenario.label} completes",
            len(st["completed_facts"]) == 2
            and st["extracted_facts"] == []
            and tuple(traced.node_sequence) == EXPECTED_NODE_SEQUENCE,
        )
