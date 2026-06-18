"""Tests for INCONCLUSIVE mechanism retry loop."""

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.mechanism_proposal import proposals_for_inconclusive, stub_mechanism
from deconstructor.skeptic.retry import retry_inconclusive
from deconstructor.skeptic.schemas import CausalClassification, RejectedHypothesis
from tests.conftest import GRID_OFF, MOTOR_STOP, ctx, fact, T0


def test_stub_mechanism_references_both():
    mech = stub_mechanism(GRID_OFF, MOTOR_STOP)
    assert "grid" in mech
    assert "motor" in mech


def test_retry_skips_when_no_inconclusive():
    engine = SkepticEngine()
    batch = engine.evaluate_batch([GRID_OFF, MOTOR_STOP])
    merged, log = retry_inconclusive(engine, [GRID_OFF, MOTOR_STOP], batch)
    codes = [e.code for e in log]
    assert "RETRY_SKIP" in codes
    assert merged is batch or len(merged.verified_edges) >= len(batch.verified_edges)


def test_retry_re_evaluates_inconclusive():
    """Vacuous mechanism -> INCONCLUSIVE; stub fill on retry may verify."""
    engine = SkepticEngine()
    first = engine.evaluate_batch([GRID_OFF, MOTOR_STOP])
    # Force an inconclusive rejection entry for retry path
    fake_rej = RejectedHypothesis(
        source_fact_id=GRID_OFF.id,
        target_fact_id=MOTOR_STOP.id,
        classification=CausalClassification.INCONCLUSIVE,
        failed_rule_ids=["R07_PROPOSED_MECHANISM"],
        reason="test",
    )
    from deconstructor.skeptic.schemas import SkepticBatchResult

    batch_with_inconclusive = SkepticBatchResult(
        verified_edges=[],
        rejected=[fake_rej],
        verdicts=first.verdicts,
    )
    proposals = proposals_for_inconclusive(
        batch_with_inconclusive.rejected, {GRID_OFF.id: GRID_OFF, MOTOR_STOP.id: MOTOR_STOP}
    )
    assert len(proposals.proposals) == 1

    merged, log = retry_inconclusive(
        engine,
        [GRID_OFF, MOTOR_STOP],
        batch_with_inconclusive,
        dry_run=True,
    )
    assert any(e.code == "RETRY_START" for e in log)
    assert len(merged.verified_edges) >= 1
