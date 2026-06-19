"""Neo4j weaver — ``--db`` 플래그 시 선택적 영속화 (Provenance Step 1)."""

from __future__ import annotations

import logging

from neo4j import Driver, GraphDatabase

from deconstructor import config
from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.provenance.types import DEFAULT_CHECK_STATUS, DEFAULT_SOURCE_TYPE
from deconstructor.storm.stress import compute_stress_delta
from deconstructor.storm.types import DEFAULT_IS_CRITICAL, DEFAULT_STRESS_LEVEL
from deconstructor.weaver.schemas import WeaverResult

logger = logging.getLogger(__name__)


def _log_prov(msg: str) -> None:
    line = f"[PROV-S1-4] {msg}"
    logger.info(line)
    print(line)


def _log_storm(step: str, msg: str) -> None:
    line = f"[STORM-S1-{step}] {msg}"
    logger.info(line)
    print(line)


class Neo4jWeaver:
    """Persist verified-edge endpoint facts and CAUSES relationships."""

    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
        )

    def close(self) -> None:
        self._driver.close()

    def _ensure_schema(self) -> None:
        with self._driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT fact_id IF NOT EXISTS
                FOR (f:Fact) REQUIRE f.id IS UNIQUE
                """
            )

    def persist(
        self,
        *,
        trigger_event: str,
        facts: list[AtomicFact],
        edges: list[CausalEdge],
        partial_run: bool = False,
    ) -> WeaverResult:
        if not edges and not facts:
            return WeaverResult(
                mode="neo4j",
                skipped_reason="no facts or edges to persist",
                partial_run=partial_run,
            )

        self._ensure_schema()
        _log_prov(f"MERGE {len(facts)} fact(s) with source_type/check_status")
        _log_storm("4", f"persist init storm fields default stress={DEFAULT_STRESS_LEVEL}")

        facts_by_id = {fact.id: fact for fact in facts}

        with self._driver.session() as session:
            for fact in facts:
                source_type = fact.source_type or DEFAULT_SOURCE_TYPE
                check_status = fact.check_status or DEFAULT_CHECK_STATUS
                _log_prov(
                    f"fact id={fact.id[:8]}.. "
                    f"source_type={source_type} check_status={check_status}"
                )
                session.run(
                    """
                    MERGE (f:Fact {id: $id})
                    SET f.subject = $subject,
                        f.state_change = $state_change,
                        f.is_atomic = true,
                        f.timestamp = $timestamp,
                        f.trigger_event = $trigger_event,
                        f.source_type = $source_type,
                        f.check_status = $check_status,
                        f.stress_level = coalesce(f.stress_level, $stress_level),
                        f.is_critical = coalesce(f.is_critical, $is_critical)
                    """,
                    id=fact.id,
                    subject=fact.subject,
                    state_change=fact.state_change,
                    timestamp=fact.timestamp.isoformat() if fact.timestamp else None,
                    trigger_event=trigger_event,
                    source_type=source_type,
                    check_status=check_status,
                    stress_level=fact.stress_level or DEFAULT_STRESS_LEVEL,
                    is_critical=fact.is_critical if fact.is_critical else DEFAULT_IS_CRITICAL,
                )

            for edge in edges:
                src = facts_by_id.get(edge.source_fact_id)
                src_type = src.source_type if src else DEFAULT_SOURCE_TYPE
                stress_delta = compute_stress_delta(src_type)
                _log_storm(
                    "5",
                    f"CAUSES {edge.source_fact_id[:8]}.. -> {edge.target_fact_id[:8]}.. "
                    f"stress_delta=+{stress_delta}",
                )
                session.run(
                    """
                    MATCH (src:Fact {id: $source_id})
                    MATCH (tgt:Fact {id: $target_id})
                    MERGE (src)-[r:CAUSES]->(tgt)
                    SET r.probability = $probability,
                        r.latency = $latency,
                        tgt.stress_level = coalesce(tgt.stress_level, 0) + $stress_delta
                    """,
                    source_id=edge.source_fact_id,
                    target_id=edge.target_fact_id,
                    probability=edge.probability,
                    latency=edge.latency,
                    stress_delta=stress_delta,
                )

        pairs = [(e.source_fact_id, e.target_fact_id) for e in edges]
        return WeaverResult(
            mode="neo4j",
            nodes_written=len(facts),
            edges_written=len(edges),
            fact_ids=[f.id for f in facts],
            edge_pairs=pairs,
            partial_run=partial_run,
        )

    def persist_ghost_facts(
        self,
        *,
        trigger_event: str,
        facts: list[AtomicFact],
    ) -> int:
        """
        A안: dropped 고스트 노드 단독 MERGE (엣지 없어도 viz용 보존).

        Step 3 fact_checker 에서 호출 예정.
        """
        if not facts:
            return 0

        self._ensure_schema()
        _log_prov(f"persist_ghost_facts count={len(facts)}")
        with self._driver.session() as session:
            for fact in facts:
                session.run(
                    """
                    MERGE (f:Fact {id: $id})
                    SET f.subject = $subject,
                        f.state_change = $state_change,
                        f.is_atomic = true,
                        f.timestamp = $timestamp,
                        f.trigger_event = $trigger_event,
                        f.source_type = $source_type,
                        f.check_status = $check_status,
                        f.stress_level = coalesce(f.stress_level, $stress_level),
                        f.is_critical = coalesce(f.is_critical, $is_critical)
                    """,
                    id=fact.id,
                    subject=fact.subject,
                    state_change=fact.state_change,
                    timestamp=fact.timestamp.isoformat() if fact.timestamp else None,
                    trigger_event=trigger_event,
                    source_type=fact.source_type,
                    check_status=fact.check_status,
                    stress_level=fact.stress_level or DEFAULT_STRESS_LEVEL,
                    is_critical=fact.is_critical if fact.is_critical else DEFAULT_IS_CRITICAL,
                )
        return len(facts)
