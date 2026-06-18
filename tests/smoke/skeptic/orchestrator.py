"""Orchestrate skeptic smoke phases."""

from __future__ import annotations

from tests.smoke.harness import StepRunner
from tests.smoke.skeptic.registry import (
    DEFAULT_SUITE_ORDER,
    run_skeptic_phase,
    run_skeptic_phases,
)


def run_skeptic_suite(
    run: StepRunner,
    *,
    with_report: bool = False,
    phases: list[int] | None = None,
) -> None:
    if phases is not None:
        numbers = list(phases)
    else:
        numbers = list(DEFAULT_SUITE_ORDER)

    if with_report and 8 not in numbers:
        numbers.append(8)

    run_skeptic_phases(run, numbers)


def run_single_skeptic_phase(run: StepRunner, number: int) -> None:
    run_skeptic_phase(run, number)
