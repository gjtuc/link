"""Phase 9 — partial_run detection."""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.pipeline.partial_run import REASON_DEPTH_CAP, detect_partial_run
from tests.smoke.harness import StepRunner


def phase_9_partial_run_isolated(run: StepRunner) -> None:
    run.section("9a detect_partial_run not partial")

    info = detect_partial_run(
        extracted_facts=[],
        completed_facts=[AtomicFact(subject="a", state_change="x -> y", is_atomic=True)],
        recursion_depth=2,
        max_recursion_depth=5,
    )
    run.check("complete run", not info.partial_run)

    run.section("9b detect_partial_run at cap")

    na = AtomicFact(subject="z", state_change="c -> e", is_atomic=False)
    info2 = detect_partial_run(
        extracted_facts=[na],
        completed_facts=[],
        recursion_depth=2,
        max_recursion_depth=2,
    )
    run.check("partial flag", info2.partial_run)
    run.check("reason code", info2.reason == REASON_DEPTH_CAP)
