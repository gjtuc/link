"""
Step 2 — Console 모드 In-memory Perfect Storm 추적
====================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from deconstructor.agents.watcher.criteria import is_storm_candidate
from deconstructor.agents.watcher.schemas import StormCandidate
from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.storm.stress import compute_stress_delta

logger = logging.getLogger(__name__)


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S2-{step}] {msg}"
    logger.info(line)
    print(line)


@dataclass
class MemoryStormNode:
    fact_id: str
    subject: str
    stress_level: int = 0
    incoming_count: int = 0
    is_critical: bool = False


@dataclass
class MemoryStormState:
    nodes: dict[str, MemoryStormNode] = field(default_factory=dict)

    def find_candidates(self) -> list[StormCandidate]:
        _log("4", "in-memory scan of simulated stress graph")
        candidates: list[StormCandidate] = []
        for node in self.nodes.values():
            if is_storm_candidate(
                stress_level=node.stress_level,
                incoming_count=node.incoming_count,
                is_critical=node.is_critical,
            ):
                candidates.append(
                    StormCandidate(
                        fact_id=node.fact_id,
                        subject=node.subject,
                        stress_level=node.stress_level,
                        incoming_count=node.incoming_count,
                    )
                )
        _log("3", f"memory candidates found={len(candidates)}")
        return candidates

    def mark_critical(self, fact_id: str) -> str:
        node = self.nodes[fact_id]
        node.is_critical = True
        return node.subject


def build_memory_storm_state(
    facts: list[AtomicFact],
    edges: list[CausalEdge],
) -> MemoryStormState:
    """verified/extracted 인과만 stress 반영, incoming 카운트는 모든 CAUSES."""
    state = MemoryStormState()
    facts_by_id = {fact.id: fact for fact in facts}

    for fact in facts:
        state.nodes[fact.id] = MemoryStormNode(
            fact_id=fact.id,
            subject=fact.subject,
            stress_level=fact.stress_level,
            is_critical=fact.is_critical,
        )

    _log("4", f"simulate {len(edges)} CAUSES edge(s) on {len(facts)} fact(s)")
    for edge in edges:
        target = state.nodes.get(edge.target_fact_id)
        if target is None:
            continue
        source = facts_by_id.get(edge.source_fact_id)
        src_type = source.source_type if source else "extracted"
        delta = compute_stress_delta(src_type)
        target.stress_level += delta
        target.incoming_count += 1
        _log(
            "4",
            f"edge -> {target.subject!r} stress+={delta} "
            f"total={target.stress_level} incoming={target.incoming_count}",
        )

    return state
