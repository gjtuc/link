"""Tests for temporal rules R03–R04."""

from datetime import timedelta

from deconstructor.skeptic.rules.temporal import (
    SimultaneousCooccurrenceRule,
    TemporalOrderingRule,
)
from deconstructor.skeptic.schemas import CausalClassification, RuleOutcome
from tests.conftest import GRID_OFF, MOTOR_STOP, T0, ctx, fact


class TestTemporalOrderingRule:
    def test_abstains_without_timestamps(self):
        a = fact("a", "x", "s -> a", timestamp=None)
        b = fact("b", "y", "s -> b", timestamp=None)
        result = TemporalOrderingRule().evaluate(ctx(a, b))
        assert result.outcome == RuleOutcome.ABSTAIN

    def test_fails_reverse_order(self):
        early = fact("e", "motor", "run -> stop", timestamp=T0)
        late = fact("l", "grid", "power -> off", timestamp=T0 + timedelta(hours=1))
        result = TemporalOrderingRule().evaluate(ctx(late, early))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_passes_correct_order(self):
        result = TemporalOrderingRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome == RuleOutcome.PASS


class TestSimultaneousCooccurrenceRule:
    def test_fails_simultaneous_without_mechanism(self):
        a = fact("a", "plant_a", "output -> zero", timestamp=T0)
        b = fact("b", "plant_b", "output -> zero", timestamp=T0)
        result = SimultaneousCooccurrenceRule().evaluate(ctx(a, b))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_passes_simultaneous_with_mechanism(self):
        a = fact("a", "plant_a", "output -> zero", timestamp=T0)
        b = fact("b", "plant_b", "output -> zero", timestamp=T0)
        result = SimultaneousCooccurrenceRule().evaluate(
            ctx(a, b, mechanism="shared grid power -> off links plant_a and plant_b")
        )
        assert result.outcome == RuleOutcome.PASS
