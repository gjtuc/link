"""Phase 4 — Routing branches."""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.routing.after_verify import route_after_verify
from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_4_routing(run: StepRunner) -> None:
    run.section("4a route: null floor -> skeptic")

    run.check(
        "empty extracted",
        route_after_verify(base_state(recursion_depth=1)) == "skeptic",
    )

    run.section("4b route: non-atomic -> deconstruct")

    non_atomic = AtomicFact(
        subject="A",
        state_change="compound -> event",
        is_atomic=False,
    )
    run.check(
        "loop back",
        route_after_verify(
            base_state(extracted_facts=[non_atomic], recursion_depth=2)
        )
        == "deconstruct",
    )

    run.section("4c route: depth cap -> skeptic")

    run.check(
        "cap exit",
        route_after_verify(
            base_state(
                extracted_facts=[non_atomic],
                recursion_depth=5,
                max_recursion_depth=5,
            )
        )
        == "skeptic",
    )
