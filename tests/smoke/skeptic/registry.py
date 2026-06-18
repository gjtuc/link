"""Skeptic smoke phase registry — run phases by number."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tests.smoke.harness import StepRunner
from tests.smoke.skeptic.phases import (
    phase_aggregator_micro,
    phase_batch_filter,
    phase_per_rule_matrix,
    phase_propagation_helpers,
    phase_registry,
    phase_report,
    phase_rule_trace_count,
    phase_scoring,
)


@dataclass(frozen=True)
class SkepticPhaseSpec:
    number: int
    label: str
    fn: Callable[[StepRunner], Any]


SKEPTIC_PHASE_REGISTRY: dict[int, SkepticPhaseSpec] = {
    1: SkepticPhaseSpec(1, "registry", phase_registry),
    2: SkepticPhaseSpec(2, "propagation", phase_propagation_helpers),
    3: SkepticPhaseSpec(3, "matrix", phase_per_rule_matrix),
    4: SkepticPhaseSpec(4, "aggregator", phase_aggregator_micro),
    5: SkepticPhaseSpec(5, "scoring", phase_scoring),
    6: SkepticPhaseSpec(6, "batch_filter", phase_batch_filter),
    7: SkepticPhaseSpec(7, "rule_trace", phase_rule_trace_count),
    8: SkepticPhaseSpec(8, "report", phase_report),
}

DEFAULT_SUITE_ORDER: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7)


def skeptic_phase_numbers() -> list[int]:
    return sorted(SKEPTIC_PHASE_REGISTRY.keys())


def skeptic_phase_labels() -> dict[int, str]:
    return {n: spec.label for n, spec in SKEPTIC_PHASE_REGISTRY.items()}


def run_skeptic_phase(run: StepRunner, number: int) -> None:
    if number not in SKEPTIC_PHASE_REGISTRY:
        valid = ", ".join(str(n) for n in skeptic_phase_numbers())
        raise ValueError(f"unknown skeptic phase {number}; valid: {valid}")
    SKEPTIC_PHASE_REGISTRY[number].fn(run)


def run_skeptic_phases(run: StepRunner, numbers: list[int]) -> None:
    for number in sorted(numbers):
        run_skeptic_phase(run, number)
