"""The Watcher orchestration — DB + Console entry points."""

from __future__ import annotations

import logging

from deconstructor.agents.watcher.memory import build_memory_storm_state
from deconstructor.agents.watcher.scan import find_storm_candidates
from deconstructor.agents.watcher.trigger import (
    trigger_storm_candidates_memory,
    trigger_storm_candidates_neo4j,
)
from deconstructor.models import AtomicFact, CausalEdge

logger = logging.getLogger(__name__)


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S2-{step}] {msg}"
    logger.info(line)
    print(line)


def run_watcher_in_memory(
    facts: list[AtomicFact],
    edges: list[CausalEdge],
) -> list[str]:
    """Console 모드: stress 시뮬 → 스캔 → 트리거."""
    if not edges:
        return []

    _log("4", "run_watcher_in_memory start")
    state = build_memory_storm_state(facts, edges)
    candidates = state.find_candidates()
    if not candidates:
        return []
    return trigger_storm_candidates_memory(state, candidates)


def run_watcher_neo4j(driver) -> list[str]:
    """DB 모드: Neo4j 스캔 → UPDATE → critical_subjects 반환."""
    with driver.session() as session:
        candidates = find_storm_candidates(session)
        if not candidates:
            return []
        return trigger_storm_candidates_neo4j(session, candidates)
