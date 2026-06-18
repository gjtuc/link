"""Phase 2 — Subject parser + stub passes."""

from __future__ import annotations

from deconstructor.dry_run.scenarios import HEADLINE_SCENARIOS
from deconstructor.dry_run.stub import (
    stub_decompose_pass_initial,
    stub_decompose_pass_refine,
)
from deconstructor.dry_run.subject import parse_subject
from tests.smoke.harness import StepRunner


def phase_2_stub_isolated(run: StepRunner, headline: str) -> None:
    run.section("2a Subject parser")

    for scenario in HEADLINE_SCENARIOS:
        got = parse_subject(scenario.headline)
        run.check(
            f"parse {scenario.label}",
            got == scenario.expected_subject,
            f"got={got!r} want={scenario.expected_subject!r}",
        )

    run.section("2b Stub pass-0 (initial)")

    initial = stub_decompose_pass_initial(headline)
    run.check("returns 1 fact", len(initial.facts) == 1)
    run.check("is_atomic=False", initial.facts[0].is_atomic is False)
    run.check(
        "subject matches parser",
        initial.facts[0].subject == parse_subject(headline),
    )

    run.section("2c Stub pass-1 (refine)")

    refined = stub_decompose_pass_refine(headline)
    run.check("returns 2 facts", len(refined.facts) == 2)
    run.check("all atomic", all(f.is_atomic for f in refined.facts))
    run.check("grid first subject", refined.facts[0].subject == "grid")
    run.check(
        "timestamps ordered",
        refined.facts[0].timestamp < refined.facts[1].timestamp,  # type: ignore[operator]
    )
