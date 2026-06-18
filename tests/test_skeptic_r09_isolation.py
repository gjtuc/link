"""Tests for R09 CrossDomainIsolationRule."""

from deconstructor.skeptic.rules.isolation import CrossDomainIsolationRule
from deconstructor.skeptic.rules.propagation import is_cross_domain_isolated
from deconstructor.skeptic.schemas import RuleOutcome
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT, ctx


def test_isolated_domains():
    assert is_cross_domain_isolated(ctx(GRID_OFF, WEATHER_HOT))


def test_not_isolated_shared_power():
    assert not is_cross_domain_isolated(ctx(GRID_OFF, MOTOR_STOP))


def test_rule_fails_isolated():
    r = CrossDomainIsolationRule().evaluate(ctx(GRID_OFF, WEATHER_HOT))
    assert r.outcome == RuleOutcome.FAIL
