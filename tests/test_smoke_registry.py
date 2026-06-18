"""Registry tests for smoke phase dispatch."""

from __future__ import annotations

import pytest

from tests.smoke.harness import StepRunner
from tests.smoke.registry import (
    FULL_SUITE_ORDER,
    phase_numbers,
    run_phase,
    run_phases,
)


def test_phase_numbers_1_to_14():
    assert phase_numbers() == list(range(1, 15))


def test_full_suite_order_matches_registry():
    assert FULL_SUITE_ORDER == tuple(range(1, 15))


def test_run_unknown_phase_raises():
    run = StepRunner()
    with pytest.raises(ValueError, match="unknown phase 99"):
        run_phase(run, 99, "headline")


def test_run_phase_1_no_headline_needed():
    run = StepRunner()
    assert run_phase(run, 1, "ignored") is None
    assert run.passed > 0


def test_run_phases_sorted():
    run = StepRunner()
    run_phases(run, [13, 1], "headline")
    assert run.passed > 0
