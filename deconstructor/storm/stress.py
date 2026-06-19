"""
Step 1 — CAUSES 엣지당 target stress delta (Micro-step S1-3)
==============================================================

오직 verified(+40) · extracted(+30)만 물리적 데미지. inferred = 0.
"""

from __future__ import annotations

import logging

from deconstructor.storm.types import (
    STRESS_WEIGHT_EXTRACTED,
    STRESS_WEIGHT_INFERRED,
    STRESS_WEIGHT_VERIFIED,
)

logger = logging.getLogger(__name__)


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S1-{step}] {msg}"
    logger.info(line)
    print(line)


def compute_stress_delta(source_type: str) -> int:
    """
    인과 원인(source)의 provenance → target stress 증분.

    inferred 및 미지 타입은 0 (차가운 현실만 반영).
    """
    normalized = (source_type or "").strip().lower()

    if normalized == "verified":
        delta = STRESS_WEIGHT_VERIFIED
        _log("3", f"compute_stress_delta verified -> +{delta}")
        return delta

    if normalized == "extracted":
        delta = STRESS_WEIGHT_EXTRACTED
        _log("3", f"compute_stress_delta extracted -> +{delta}")
        return delta

    _log("3", f"compute_stress_delta {normalized or 'unknown'} -> +{STRESS_WEIGHT_INFERRED} (ignored)")
    return STRESS_WEIGHT_INFERRED
