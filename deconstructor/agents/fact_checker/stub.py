"""
Step 3 — Fact-Checker dry-run stub (Micro-step CHECK-S3-stub)
=============================================================

Step 2 stub 3가설: 앞 2개 Promote, 주식 폭락 Drop.
"""

from __future__ import annotations

import logging

from deconstructor.agents.fact_checker.schemas import VerificationVerdict
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)

FINANCIAL_DROP_KEYWORDS = (
    "equity",
    "index",
    "stock",
    "price",
    "percent",
    "share",
    "주식",
    "폭락",
    "증시",
)


def _log(msg: str) -> None:
    line = f"[CHECK-S3-stub] {msg}"
    logger.info(line)
    print(line)


def stub_verify_hypothesis(fact: AtomicFact) -> VerificationVerdict:
    """
    Dry-run: 물리 가설 통과, 금융 가설 탈락.

    Matches dreamer stub hypothesis #3 (equity index / price decline).
    """
    blob = f"{fact.subject} {fact.state_change}".lower()
    if any(k in blob for k in FINANCIAL_DROP_KEYWORDS):
        _log(f"DROP financial/non-physical hypothesis subject={fact.subject!r}")
        return VerificationVerdict(
            accepted=False,
            reason=(
                "non-physical financial/market claim - no operational state change "
                "corroborated (stub drop for equity/price hypothesis)"
            ),
        )

    _log(f"PROMOTE physical hypothesis subject={fact.subject!r}")
    return VerificationVerdict(
        accepted=True,
        reason="stub: physical ripple hypothesis accepted for dry-run",
    )
