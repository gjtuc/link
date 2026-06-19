"""Step 3 — promote/drop apply unit tests."""

from datetime import datetime

from deconstructor.agents.fact_checker.apply import drop_fact, promote_fact
from deconstructor.agents.fact_checker.schemas import VerificationVerdict
from deconstructor.models import AtomicFact


def test_promote_sets_inferred_promoted():
    fact = AtomicFact(
        subject="factory line",
        state_change="operation -> halted",
        timestamp=datetime(2026, 1, 1, 10, 5, 0),
        source_type="inferred",
        check_status="pending",
    )
    promoted = promote_fact(fact, VerificationVerdict(accepted=True, reason="stub ok"))
    assert promoted.source_type == "inferred"
    assert promoted.check_status == "promoted"


def test_drop_sets_ghost_inferred_dropped():
    fact = AtomicFact(
        subject="equity index",
        state_change="price -> decline",
        source_type="inferred",
        check_status="pending",
    )
    dropped = drop_fact(fact, VerificationVerdict(accepted=False, reason="no evidence"))
    assert dropped.ghost_fact.source_type == "inferred"
    assert dropped.ghost_fact.check_status == "dropped"
    assert dropped.drop_reason == "no evidence"
