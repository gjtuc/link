"""Tests for R08 NarrativeLeakRule."""

from deconstructor.skeptic.rules.narrative import NarrativeLeakRule, find_narrative_leaks
from deconstructor.skeptic.schemas import CausalClassification, RuleOutcome
from tests.conftest import MOTOR_STOP, ctx, fact, T0


def test_find_narrative_leaks_bullish():
    assert "bullish" in find_narrative_leaks("price bullish spike")


def test_rule_rejects_narrative():
    bad = fact("n", "stock", "price -> bullish_move", timestamp=T0)
    r = NarrativeLeakRule().evaluate(ctx(bad, MOTOR_STOP))
    assert r.outcome == RuleOutcome.FAIL
    assert r.classification == CausalClassification.CORRELATION
