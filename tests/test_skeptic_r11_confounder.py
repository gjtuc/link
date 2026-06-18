"""Tests for R11 PostHocLagRule."""

from deconstructor.skeptic.rules.confounder import PostHocLagRule
from deconstructor.skeptic.schemas import RuleOutcome
from tests.conftest import GRID_OFF, MOTOR_STOP, T0, ctx, fact


def test_positive_lag_passes():
    r = PostHocLagRule().evaluate(ctx(GRID_OFF, MOTOR_STOP))
    assert r.outcome == RuleOutcome.PASS


def test_zero_lag_cross_domain_fails():
    a = fact("a", "alpha", "x -> 1", timestamp=T0)
    b = fact("b", "beta", "y -> 2", timestamp=T0)
    r = PostHocLagRule().evaluate(ctx(a, b))
    assert r.outcome == RuleOutcome.FAIL
