"""Tests for R10 EntityStateChainRule."""

from datetime import timedelta

from deconstructor.skeptic.rules.chain import EntityStateChainRule
from deconstructor.skeptic.schemas import RuleOutcome
from tests.conftest import T0, ctx, fact


def test_entity_chain_passes():
    pump = fact("p1", "pump", "state -> running", timestamp=T0)
    stop = fact("p2", "pump", "state -> stopped", timestamp=T0 + timedelta(seconds=5))
    r = EntityStateChainRule().evaluate(ctx(pump, stop))
    assert r.outcome == RuleOutcome.PASS


def test_entity_chain_abstains_different_subject():
    a = fact("a", "alpha", "x -> 1", timestamp=T0)
    b = fact("b", "beta", "y -> 2", timestamp=T0)
    r = EntityStateChainRule().evaluate(ctx(a, b))
    assert r.outcome == RuleOutcome.ABSTAIN
