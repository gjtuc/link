"""Smoke phase registry — run phases by number."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tests.smoke.harness import StepRunner
from tests.smoke.phases import (
    phase_1_pydantic,
    phase_10_weaver_dry,
    phase_11_report_sections,
    phase_12_llm_deconstruct,
    phase_13_truth_table,
    phase_14_mechanism_llm,
    phase_2_stub_isolated,
    phase_3_nodes_isolated,
    phase_4_routing,
    phase_5_traced_pipeline,
    phase_6_matrix,
    phase_7_package_split,
    phase_8_depth_cap,
    phase_9_partial_run_isolated,
)


@dataclass(frozen=True)
class PhaseSpec:
    """One smoke phase callable and metadata."""

    number: int
    label: str
    fn: Callable[..., Any]
    needs_headline: bool = False
    returns_report: bool = False


PHASE_REGISTRY: dict[int, PhaseSpec] = {
    1: PhaseSpec(1, "pydantic", phase_1_pydantic),
    2: PhaseSpec(2, "stub", phase_2_stub_isolated, needs_headline=True),
    3: PhaseSpec(3, "nodes", phase_3_nodes_isolated, needs_headline=True),
    4: PhaseSpec(4, "routing", phase_4_routing),
    5: PhaseSpec(5, "pipeline", phase_5_traced_pipeline, needs_headline=True, returns_report=True),
    6: PhaseSpec(6, "matrix", phase_6_matrix),
    7: PhaseSpec(7, "package", phase_7_package_split),
    8: PhaseSpec(8, "depth_cap", phase_8_depth_cap, returns_report=True),
    9: PhaseSpec(9, "partial", phase_9_partial_run_isolated),
    10: PhaseSpec(10, "weaver", phase_10_weaver_dry, needs_headline=True),
    11: PhaseSpec(11, "report", phase_11_report_sections, needs_headline=True),
    12: PhaseSpec(12, "llm_deconstruct", phase_12_llm_deconstruct),
    13: PhaseSpec(13, "truth_table", phase_13_truth_table),
    14: PhaseSpec(14, "mechanism", phase_14_mechanism_llm),
}

FULL_SUITE_ORDER: tuple[int, ...] = tuple(PHASE_REGISTRY.keys())


def phase_numbers() -> list[int]:
    return sorted(PHASE_REGISTRY.keys())


def phase_labels() -> dict[int, str]:
    return {n: spec.label for n, spec in PHASE_REGISTRY.items()}


def run_phase(
    run: StepRunner,
    number: int,
    headline: str,
) -> str | None:
    """Run a single phase by number; return report text if phase produces one."""
    if number not in PHASE_REGISTRY:
        valid = ", ".join(str(n) for n in phase_numbers())
        raise ValueError(f"unknown phase {number}; valid: {valid}")

    spec = PHASE_REGISTRY[number]
    if spec.needs_headline:
        result = spec.fn(run, headline)
    else:
        result = spec.fn(run)

    if spec.returns_report:
        return result
    return None


def run_phases(
    run: StepRunner,
    numbers: list[int],
    headline: str,
) -> str | None:
    """Run selected phases in ascending order; last report wins."""
    report: str | None = None
    for number in sorted(numbers):
        maybe_report = run_phase(run, number, headline)
        if maybe_report is not None:
            report = maybe_report
    return report
