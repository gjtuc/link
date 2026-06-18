"""Skeptic smoke phase 2 — propagation helpers."""

from __future__ import annotations

from deconstructor.skeptic.rules.propagation import (
    has_propagation_path,
    is_cross_domain_isolated,
    shared_tokens,
)
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT, ctx
from tests.smoke.harness import StepRunner


def phase_propagation_helpers(run: StepRunner) -> None:
    run.section("2 Propagation helpers")
    c = ctx(GRID_OFF, MOTOR_STOP)
    run.ok("grid-motor path", has_propagation_path(c))
    run.ok("grid-motor shared tokens", len(shared_tokens(c)) > 0)
    run.ok("grid-weather isolated", is_cross_domain_isolated(ctx(GRID_OFF, WEATHER_HOT)))
