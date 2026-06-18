"""Phase 14 — Mechanism proposal LLM package."""

from __future__ import annotations

from unittest.mock import MagicMock

from deconstructor.skeptic.mechanism_proposal import (
    MechanismProposal,
    fill_mechanisms,
    invoke_mechanism_proposal,
)
from deconstructor.skeptic.schemas import CausalClassification, RejectedHypothesis
from tests.conftest import GRID_OFF, MOTOR_STOP
from tests.smoke.harness import StepRunner


def phase_14_mechanism_llm(run: StepRunner) -> None:
    rej = RejectedHypothesis(
        source_fact_id=GRID_OFF.id,
        target_fact_id=MOTOR_STOP.id,
        classification=CausalClassification.INCONCLUSIVE,
        failed_rule_ids=["R07"],
        reason="test",
    )
    idx = {GRID_OFF.id: GRID_OFF, MOTOR_STOP.id: MOTOR_STOP}

    run.section("14a stub fill (dry_run)")

    stub_batch = fill_mechanisms([rej], idx, dry_run=True)
    run.check("one proposal", len(stub_batch.proposals) == 1)
    run.check(
        "references grid",
        "grid" in stub_batch.proposals[0].proposed_mechanism,
    )

    run.section("14b LLM fill (mock)")

    mock = MagicMock()
    mock.invoke.return_value = MechanismProposal(
        source_fact_id=GRID_OFF.id,
        target_fact_id=MOTOR_STOP.id,
        proposed_mechanism="grid outage stops motor supply",
    )
    llm_batch = fill_mechanisms([rej], idx, dry_run=False, llm=mock)
    run.check("llm proposal count", len(llm_batch.proposals) == 1)
    run.check("mock called", mock.invoke.called)

    run.section("14c single-pair invoke")

    p = invoke_mechanism_proposal(GRID_OFF, MOTOR_STOP, llm=mock)
    run.check("ids wired", p.source_fact_id == GRID_OFF.id)
