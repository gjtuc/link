"""
Step 1 — Storm 임계점 상수 (Micro-step S1-2)
============================================

verified / extracted 만 타겟 stress에 기여. inferred = 0 (설계 결정).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

STRESS_WEIGHT_VERIFIED = 40
STRESS_WEIGHT_EXTRACTED = 30
STRESS_WEIGHT_INFERRED = 0
STRESS_THRESHOLD = 100
DEFAULT_STRESS_LEVEL = 0
DEFAULT_IS_CRITICAL = False
MIN_INCOMING_CAUSES_FOR_STORM = 2


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S1-{step}] {msg}"
    logger.info(line)
    print(line)


_log("1", "AtomicFact storm defaults stress_level=0 is_critical=False")
_log(
    "2",
    f"weights verified=+{STRESS_WEIGHT_VERIFIED} "
    f"extracted=+{STRESS_WEIGHT_EXTRACTED} "
    f"inferred=+{STRESS_WEIGHT_INFERRED} "
    f"threshold={STRESS_THRESHOLD}",
)
