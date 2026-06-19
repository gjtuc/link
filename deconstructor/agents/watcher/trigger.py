"""
Step 3 — Perfect Storm 트리거 (Micro-step S3-*)
===============================================
"""

from __future__ import annotations

import logging
import sys

from deconstructor.agents.watcher.memory import MemoryStormState
from deconstructor.agents.watcher.schemas import StormCandidate

logger = logging.getLogger(__name__)

ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[91m"
ANSI_RESET = "\033[0m"

MARK_CRITICAL_CYPHER = """
MATCH (t:Fact {id: $id})
SET t.is_critical = true
RETURN t.subject AS subject
"""


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S3-{step}] {msg}"
    logger.info(line)
    print(line)


def emit_storm_trigger(subject: str) -> None:
    """터미널에 붉은색 [STORM-S3-TRIGGER] 경고 출력."""
    message = f"[STORM-S3-TRIGGER] Perfect Storm Detected on node: {subject}"
    colored = f"{ANSI_BOLD}{ANSI_RED}{message}{ANSI_RESET}"
    if sys.stdout.isatty():
        print(colored)
    else:
        # pytest·파이프 환경: ANSI + plain marker 모두 유지
        print(colored)
    logger.warning(message)


def trigger_storm_candidates_neo4j(
    session,
    candidates: list[StormCandidate],
) -> list[str]:
    """DB 모드: is_critical=True UPDATE + 붉은 경고."""
    subjects: list[str] = []
    for candidate in candidates:
        _log("1", f"SET is_critical=true id={candidate.fact_id[:8]}.. subject={candidate.subject!r}")
        row = session.run(
            MARK_CRITICAL_CYPHER,
            id=candidate.fact_id,
        ).single()
        subject = (row["subject"] if row else None) or candidate.subject
        emit_storm_trigger(subject)
        subjects.append(subject)
    _log("2", f"triggered {len(subjects)} critical node(s) in Neo4j")
    return subjects


def trigger_storm_candidates_memory(
    state: MemoryStormState,
    candidates: list[StormCandidate],
) -> list[str]:
    """Console 모드: 객체 상태 변경 + 붉은 경고."""
    subjects: list[str] = []
    for candidate in candidates:
        _log("1", f"memory SET is_critical=true subject={candidate.subject!r}")
        subject = state.mark_critical(candidate.fact_id)
        emit_storm_trigger(subject)
        subjects.append(subject)
    _log("2", f"triggered {len(subjects)} critical node(s) in memory")
    return subjects
