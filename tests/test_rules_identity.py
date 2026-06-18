"""Tests for identity rules R01–R02."""

from deconstructor.skeptic.rules.identity import DuplicateFactPairRule, NoSelfLoopRule
from deconstructor.skeptic.schemas import CausalClassification, RuleOutcome
from tests.conftest import GRID_OFF, MOTOR_STOP, ctx


class TestNoSelfLoopRule:
    def test_rejects_self_loop(self):
        result = NoSelfLoopRule().evaluate(ctx(GRID_OFF, GRID_OFF))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_passes_distinct_pair(self):
        result = NoSelfLoopRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome == RuleOutcome.PASS


class TestDuplicateFactPairRule:
    def test_rejects_identical_crumbs(self):
        twin = GRID_OFF.model_copy(deep=True)
        twin.id = "f1-copy"
        result = DuplicateFactPairRule().evaluate(ctx(GRID_OFF, twin))
        assert result.outcome == RuleOutcome.FAIL
        assert result.classification == CausalClassification.CORRELATION

    def test_passes_different_crumbs(self):
        result = DuplicateFactPairRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
        assert result.outcome == RuleOutcome.PASS
