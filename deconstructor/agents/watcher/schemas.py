"""Storm candidate DTO for The Watcher scan/trigger pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StormCandidate:
    """A target node that crossed the Perfect Storm threshold."""

    fact_id: str
    subject: str
    stress_level: int
    incoming_count: int
