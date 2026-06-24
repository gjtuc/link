"""Shared fixtures for skeptic tests."""

from __future__ import annotations

import pytest

from datetime import datetime, timedelta

from deconstructor.models import AtomicFact
from deconstructor.skeptic.schemas import CausalHypothesis, RuleContext

T0 = datetime(2026, 6, 1, 10, 0, 0)


def pytest_configure(config):
    config.addinivalue_line("markers", "expensive: live LLM E2E (Sprint 3, optional)")
    config.addinivalue_line("markers", "live: live LLM probe (optional, e.g. dreamer breadth)")


def fact(
    id: str,
    subject: str,
    state_change: str,
    *,
    timestamp: datetime | None = None,
    is_atomic: bool = True,
) -> AtomicFact:
    return AtomicFact(
        id=id,
        subject=subject,
        state_change=state_change,
        timestamp=timestamp,
        is_atomic=is_atomic,
    )


def ctx(
    source: AtomicFact,
    target: AtomicFact,
    mechanism: str = "",
) -> RuleContext:
    return RuleContext(
        source=source,
        target=target,
        hypothesis=CausalHypothesis(
            source_fact_id=source.id,
            target_fact_id=target.id,
            proposed_mechanism=mechanism,
        ),
    )


GRID_OFF = fact("f1", "grid", "power -> off", timestamp=T0)
MOTOR_STOP = fact(
    "f2",
    "motor",
    "power_supply -> interrupted",
    timestamp=T0 + timedelta(minutes=2),
)
WEATHER_HOT = fact("f3", "weather", "temperature -> high", timestamp=T0)
