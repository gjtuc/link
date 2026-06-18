"""Skeptic smoke phase 8 — formatted batch report."""

from __future__ import annotations

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.report import format_skeptic_report
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT
from tests.smoke.harness import StepRunner


def phase_report(run: StepRunner) -> None:
    run.section("8 Skeptic report")
    batch = SkepticEngine().evaluate_batch([GRID_OFF, MOTOR_STOP, WEATHER_HOT])
    text = format_skeptic_report(batch)
    run.check("report non-empty", len(text) > 50)
    print("\n" + text)
