"""
Step 2 — Neo4j Perfect Storm 스캔 (Micro-step S2-*)
===================================================
"""

from __future__ import annotations

import logging

from deconstructor.agents.watcher.schemas import StormCandidate
from deconstructor.storm.types import MIN_INCOMING_CAUSES_FOR_STORM, STRESS_THRESHOLD

logger = logging.getLogger(__name__)

STORM_CANDIDATES_CYPHER = """
MATCH (t:Fact)
WHERE coalesce(t.is_critical, false) = false
  AND (
    size((t)<-[:CAUSES]-()) >= $min_incoming
    OR coalesce(t.stress_level, 0) > $stress_threshold
  )
RETURN t.id AS id,
       t.subject AS subject,
       coalesce(t.stress_level, 0) AS stress_level,
       size((t)<-[:CAUSES]-()) AS incoming_count
ORDER BY stress_level DESC, incoming_count DESC
"""


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S2-{step}] {msg}"
    logger.info(line)
    print(line)


def find_storm_candidates(session) -> list[StormCandidate]:
    """
    Neo4j에서 임계점 돌파 후보 노드를 스캔.

    조건: is_critical=false AND (incoming CAUSES >= 2 OR stress_level > 100).
    """
    _log(
        "1",
        f"scan Neo4j targets incoming>={MIN_INCOMING_CAUSES_FOR_STORM} "
        f"OR stress>{STRESS_THRESHOLD}",
    )
    rows = session.run(
        STORM_CANDIDATES_CYPHER,
        min_incoming=MIN_INCOMING_CAUSES_FOR_STORM,
        stress_threshold=STRESS_THRESHOLD,
    ).data()
    _log("2", f"stress threshold strictly greater than {STRESS_THRESHOLD}")
    candidates = [
        StormCandidate(
            fact_id=row["id"],
            subject=row["subject"] or "",
            stress_level=int(row["stress_level"] or 0),
            incoming_count=int(row["incoming_count"] or 0),
        )
        for row in rows
    ]
    _log(
        "3",
        f"candidates found={len(candidates)} (is_critical=false filter applied)",
    )
    return candidates
