"""Tests for skeptic aggregator micro-steps."""

from deconstructor.skeptic.aggregator import aggregate_verdict
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleOutcome,
)


def test_a1_correlation_fail_first():
    results = [
        RuleCheckResult(rule_id="R01", outcome=RuleOutcome.PASS),
        RuleCheckResult(
            rule_id="R09",
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.CORRELATION,
            reason="isolated",
        ),
    ]
    cls, ok, trace = aggregate_verdict(results)
    assert not ok
    assert cls == CausalClassification.CORRELATION
    assert trace[0].step_id == "A1"


def test_a4_all_abstain():
    results = [
        RuleCheckResult(rule_id="R07", outcome=RuleOutcome.ABSTAIN),
    ]
    cls, ok, trace = aggregate_verdict(results)
    assert not ok
    assert cls == CausalClassification.INCONCLUSIVE
    assert trace[0].step_id == "A4"


def test_a5_unanimous_pass():
    results = [
        RuleCheckResult(rule_id="R01", outcome=RuleOutcome.PASS),
        RuleCheckResult(rule_id="R06", outcome=RuleOutcome.PASS),
    ]
    cls, ok, trace = aggregate_verdict(results)
    assert ok
    assert cls == CausalClassification.CAUSAL
    assert trace[0].step_id == "A5"
