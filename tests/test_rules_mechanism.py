"""Tests for mechanism and common-cause rules R05–R07."""

from deconstructor.skeptic.rules.common_cause import CommonCausePatternRule
from deconstructor.skeptic.rules.mechanism import (
    MechanismPlausibilityRule,
    ProposedMechanismRule,
)
from deconstructor.skeptic.schemas import CausalClassification, RuleOutcome
from tests.conftest import GRID_OFF, MOTOR_STOP, T0, WEATHER_HOT, ctx, fact


class TestCommonCausePatternRule:
    def test_fails_parallel_unrelated_effects(self):
        a = fact("a", "line_a", "throughput -> zero", timestamp=T0)
        b = fact("b", "line_b", "throughput -> zero", timestamp=T0)
        result = CommonCausePatternRule().evaluate(ctx(a, b))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_abstains_same_subject(self):
        result = CommonCausePatternRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome in (RuleOutcome.ABSTAIN, RuleOutcome.PASS)


class TestMechanismPlausibilityRule:
    def test_passes_propagation_chain(self):
        result = MechanismPlausibilityRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome == RuleOutcome.PASS

    def test_fails_unrelated_crumbs(self):
        result = MechanismPlausibilityRule().evaluate(ctx(GRID_OFF, WEATHER_HOT))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_passes_with_explicit_mechanism(self):
        result = MechanismPlausibilityRule().evaluate(
            ctx(GRID_OFF, WEATHER_HOT, mechanism="grid heat load rises with temperature")
        )
        assert result.outcome == RuleOutcome.PASS


class TestProposedMechanismRule:
    def test_abstains_when_empty(self):
        result = ProposedMechanismRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome == RuleOutcome.ABSTAIN

    def test_passes_when_references_both(self):
        mech = "grid power -> off causes motor operation -> stopped"
        result = ProposedMechanismRule().evaluate(ctx(GRID_OFF, MOTOR_STOP, mechanism=mech))
        assert result.outcome == RuleOutcome.PASS

    def test_fails_vacuous_mechanism(self):
        result = ProposedMechanismRule().evaluate(
            ctx(GRID_OFF, MOTOR_STOP, mechanism="something happened elsewhere")
        )
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.INCONCLUSIVE
