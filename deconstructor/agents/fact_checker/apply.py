"""
Step 3 — Promote / Drop 변환 (Micro-step CHECK-S3-apply)
========================================================
"""

from __future__ import annotations

import logging

from deconstructor.agents.fact_checker.schemas import DroppedHypothesis, VerificationVerdict
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S3-apply] {msg}"
    logger.info(line)
    from deconstructor.cli.print_util import safe_print
    safe_print(line)


def promote_fact(fact: AtomicFact, verdict: VerificationVerdict) -> AtomicFact:
    """합격: source_type=verified, check_status=active."""
    promoted = fact.model_copy(
        update={
            "source_type": "verified",
            "check_status": "active",
            "reasoning": f"{fact.reasoning} | verified: {verdict.reason}".strip(" |"),
        }
    )
    _log(
        f"PROMOTE id={promoted.id[:8]}.. "
        f"verified/active reason={verdict.reason[:60]!r}"
    )
    return promoted


def drop_fact(fact: AtomicFact, verdict: VerificationVerdict) -> DroppedHypothesis:
    """탈락: source_type=inferred, check_status=dropped (고스트)."""
    ghost = fact.model_copy(
        update={
            "source_type": "inferred",
            "check_status": "dropped",
        }
    )
    _log(
        f"DROP id={ghost.id[:8]}.. "
        f"inferred/dropped reason={verdict.reason[:80]!r}"
    )
    return DroppedHypothesis(
        fact_id=fact.id,
        subject=fact.subject,
        state_change=fact.state_change,
        drop_reason=verdict.reason,
        ghost_fact=ghost,
    )
