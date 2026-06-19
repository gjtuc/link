"""Step 1 — Storm data model defaults ([STORM-S1-1])."""

import pytest

from deconstructor.models import AtomicFact


def test_atomic_fact_stress_level_defaults_zero():
    fact = AtomicFact(subject="grid", state_change="power -> off", is_atomic=True)
    assert fact.stress_level == 0


def test_atomic_fact_is_critical_defaults_false():
    fact = AtomicFact(subject="factory", state_change="output -> halted", is_atomic=True)
    assert fact.is_critical is False


def test_atomic_fact_stress_level_rejects_negative():
    with pytest.raises(ValueError):
        AtomicFact(
            subject="grid",
            state_change="power -> off",
            is_atomic=True,
            stress_level=-1,
        )


def test_atomic_fact_preserves_explicit_storm_fields():
    fact = AtomicFact(
        subject="A공장",
        state_change="power -> lost",
        is_atomic=True,
        stress_level=70,
        is_critical=True,
    )
    assert fact.stress_level == 70
    assert fact.is_critical is True
