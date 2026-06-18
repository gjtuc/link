"""Orchestrate pipeline smoke phases."""

from __future__ import annotations

from deconstructor.dry_run.scenarios import DEPTH_CAP_SCENARIO, DEFAULT_HEADLINE
from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.report import state_to_json
from tests.smoke.harness import StepRunner
from tests.smoke.registry import FULL_SUITE_ORDER, run_phase, run_phases


def run_depth_cap_only(run: StepRunner) -> str:
    report = run_phase(run, 8, DEFAULT_HEADLINE)
    print("\n== 8 Console report (depth cap) ==")
    assert report is not None
    return report


def run_full_suite(
    run: StepRunner,
    headline: str,
    *,
    matrix: bool = False,
) -> str:
    numbers = list(FULL_SUITE_ORDER)
    if not matrix:
        numbers = [n for n in numbers if n != 6]
    report = run_phases(run, numbers, headline)
    print("\n== 7 Console report ==")
    assert report is not None
    return report


def run_single_phase(run: StepRunner, number: int, headline: str) -> str | None:
    """Run one phase by number (--phase N)."""
    return run_phase(run, number, headline)


def dump_json(*, depth_cap: bool, headline: str) -> str:
    h = DEPTH_CAP_SCENARIO.headline if depth_cap else headline
    cap = DEPTH_CAP_SCENARIO.max_recursion_depth if depth_cap else None
    traced = run_pipeline_traced(h, dry_run=True, max_recursion_depth=cap)
    return state_to_json(traced.final_state)


def default_headline() -> str:
    return DEFAULT_HEADLINE
