"""
Step 2 — Perfect Storm 후보 판정 (순수 로직)
============================================

DB·Console 양쪽 Watcher가 동일 조건을 공유한다.
"""

from __future__ import annotations

from deconstructor.storm.types import (
    MIN_INCOMING_CAUSES_FOR_STORM,
    STRESS_THRESHOLD,
)


def is_storm_candidate(
    *,
    stress_level: int,
    incoming_count: int,
    is_critical: bool,
) -> bool:
    """incoming >= 2 OR stress > 100, and not already critical."""
    if is_critical:
        return False
    if incoming_count >= MIN_INCOMING_CAUSES_FOR_STORM:
        return True
    return stress_level > STRESS_THRESHOLD
