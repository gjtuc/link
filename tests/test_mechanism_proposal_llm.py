"""Mechanism proposal package — stub vs LLM paths."""

from __future__ import annotations

from unittest.mock import MagicMock

from deconstructor.skeptic.mechanism_proposal import (
    MechanismProposal,
    fill_mechanisms,
    invoke_mechanism_proposal,
    propose_mechanisms_llm,
)
from deconstructor.skeptic.schemas import CausalClassification, RejectedHypothesis
from tests.conftest import GRID_OFF, MOTOR_STOP


def _inconclusive_rej():
    return RejectedHypothesis(
        source_fact_id=GRID_OFF.id,
        target_fact_id=MOTOR_STOP.id,
        classification=CausalClassification.INCONCLUSIVE,
        failed_rule_ids=["R07_PROPOSED_MECHANISM"],
        reason="vacuous",
    )


def test_fill_mechanisms_stub_path():
    batch = fill_mechanisms(
        [_inconclusive_rej()],
        {GRID_OFF.id: GRID_OFF, MOTOR_STOP.id: MOTOR_STOP},
        dry_run=True,
    )
    assert len(batch.proposals) == 1
    assert "grid" in batch.proposals[0].proposed_mechanism


def test_fill_mechanisms_skips_correlation():
    corr = RejectedHypothesis(
        source_fact_id=GRID_OFF.id,
        target_fact_id=MOTOR_STOP.id,
        classification=CausalClassification.CORRELATION,
        failed_rule_ids=["R01"],
        reason="corr",
    )
    batch = fill_mechanisms(
        [corr],
        {GRID_OFF.id: GRID_OFF, MOTOR_STOP.id: MOTOR_STOP},
        dry_run=True,
    )
    assert batch.proposals == []


def test_invoke_mechanism_proposal_mock_llm():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MechanismProposal(
        source_fact_id="x",
        target_fact_id="y",
        proposed_mechanism="grid loss cuts motor supply",
    )

    proposal = invoke_mechanism_proposal(GRID_OFF, MOTOR_STOP, llm=mock_llm)

    mock_llm.invoke.assert_called_once()
    assert proposal.source_fact_id == GRID_OFF.id
    assert proposal.target_fact_id == MOTOR_STOP.id
    assert "grid" in proposal.proposed_mechanism


def test_propose_mechanisms_llm_batch():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MechanismProposal(
        source_fact_id="a",
        target_fact_id="b",
        proposed_mechanism="mechanical link",
    )

    batch = propose_mechanisms_llm([(GRID_OFF, MOTOR_STOP)], llm=mock_llm)

    assert len(batch.proposals) == 1
    assert batch.proposals[0].proposed_mechanism == "mechanical link"


def test_fill_mechanisms_llm_path():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MechanismProposal(
        source_fact_id="a",
        target_fact_id="b",
        proposed_mechanism="LLM mechanism text",
    )

    batch = fill_mechanisms(
        [_inconclusive_rej()],
        {GRID_OFF.id: GRID_OFF, MOTOR_STOP.id: MOTOR_STOP},
        dry_run=False,
        llm=mock_llm,
    )

    assert len(batch.proposals) == 1
    assert batch.proposals[0].proposed_mechanism == "LLM mechanism text"
