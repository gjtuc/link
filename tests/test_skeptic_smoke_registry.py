"""Registry tests for skeptic smoke phase dispatch."""

from __future__ import annotations

import pytest

from tests.smoke.harness import StepRunner
from tests.smoke.skeptic.registry import (
    DEFAULT_SUITE_ORDER,
    run_skeptic_phase,
    run_skeptic_phases,
    skeptic_phase_numbers,
)


def test_skeptic_phase_numbers_1_to_8():
    assert skeptic_phase_numbers() == list(range(1, 9))


def test_default_suite_is_1_through_7():
    assert DEFAULT_SUITE_ORDER == tuple(range(1, 8))


def test_run_unknown_skeptic_phase_raises():
    run = StepRunner()
    with pytest.raises(ValueError, match="unknown skeptic phase 99"):
        run_skeptic_phase(run, 99)


def test_run_skeptic_phase_1():
    run = StepRunner()
    run_skeptic_phase(run, 1)
    assert run.passed >= 4


def test_run_skeptic_phases_sorted():
    run = StepRunner()
    run_skeptic_phases(run, [7, 1])
    assert run.passed >= 6
