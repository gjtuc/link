"""
Human hypothesis — Neo4j 읽기·단건 MERGE (MVP)
==============================================

전체 파이프라인(weaver)을 다시 돌리지 않고 **가설 1건**만 영속화한다.
스키마 필드는 ``Neo4jWeaver.persist`` / ``persist_ghost_facts`` 와 동기화.

Micro-steps (로그 prefix ``[HYP-MVP-S*]``)
-----------------------------------------
  S1  anchor Fact 존재·provenance 검증
  S2  human inferred Fact MERGE
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from neo4j import GraphDatabase

from deconstructor import config
from deconstructor.models import AtomicFact
from deconstructor.provenance.types import DEFAULT_CHECK_STATUS, DEFAULT_SOURCE_TYPE
from deconstructor.web.graph_context import get_last_analysis_run_id
from deconstructor.storm.types import DEFAULT_IS_CRITICAL, DEFAULT_STRESS_LEVEL

logger = logging.getLogger(__name__)

# MVP: 우클릭 가설 추가는 **파란 extracted·active** 에서만 허용
ANCHOR_SOURCE_TYPES = frozenset({"extracted"})
ANCHOR_CHECK_STATUSES = frozenset({"active"})


@dataclass(frozen=True)
class AnchorFactRecord:
    """Neo4j 에서 읽은 원천 노드 — anchor 검증용."""

    id: str
    subject: str
    source_type: str
    check_status: str
    timestamp: datetime | None


class HumanHypothesisStoreError(ValueError):
    """anchor 없음·provenance 불일치 등 클라이언트 수정 가능 오류."""


def _log(step: str, msg: str) -> None:
    line = f"[HYP-MVP-S{step}] {msg}"
    logger.info(line)
    print(line)


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_anchor_fact(anchor_fact_id: str) -> AnchorFactRecord:
    """
    원천 Fact 1건 조회. 없으면 ``HumanHypothesisStoreError``.

    Raises:
        HumanHypothesisStoreError: id 미존재 또는 extracted/active 가 아님.
    """
    anchor_fact_id = anchor_fact_id.strip()
    if not anchor_fact_id:
        raise HumanHypothesisStoreError("anchor_fact_id 가 비어 있습니다.")

    _log("1", f"load anchor id={anchor_fact_id[:8]}..")
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )
    try:
        with driver.session() as session:
            row = session.run(
                """
                MATCH (f:Fact {id: $id})
                RETURN f.id AS id,
                       f.subject AS subject,
                       coalesce(f.source_type, $default_source) AS source_type,
                       coalesce(f.check_status, $default_check) AS check_status,
                       f.timestamp AS timestamp
                """,
                id=anchor_fact_id,
                default_source=DEFAULT_SOURCE_TYPE,
                default_check=DEFAULT_CHECK_STATUS,
            ).single()
    finally:
        driver.close()

    if row is None:
        raise HumanHypothesisStoreError(
            f"원천 노드를 찾을 수 없습니다: {anchor_fact_id}"
        )

    source_type = row["source_type"] or DEFAULT_SOURCE_TYPE
    check_status = row["check_status"] or DEFAULT_CHECK_STATUS
    if source_type not in ANCHOR_SOURCE_TYPES:
        raise HumanHypothesisStoreError(
            f"가설은 파란(extracted) 노드에서만 추가할 수 있습니다 "
            f"(현재 source_type={source_type!r})."
        )
    if check_status not in ANCHOR_CHECK_STATUSES:
        raise HumanHypothesisStoreError(
            f"가설을 추가할 수 없는 노드 상태입니다 "
            f"(check_status={check_status!r})."
        )

    _log(
        "1",
        f"anchor ok subject={row['subject']!r} "
        f"source_type={source_type} check_status={check_status}",
    )
    return AnchorFactRecord(
        id=row["id"],
        subject=row["subject"] or "",
        source_type=source_type,
        check_status=check_status,
        timestamp=_parse_timestamp(row["timestamp"]),
    )


def merge_human_hypothesis_fact(
    fact: AtomicFact,
    *,
    trigger_event: str = "human_hypothesis",
) -> str:
    """
    사용자 가설 AtomicFact 1건 MERGE. 새 id 반환.

    ``author`` 필드는 Neo4j ``f.author`` 로 저장 (레거시 fact 는 null).
    """
    _log("2", f"MERGE human fact id={fact.id[:8]}.. anchor={fact.anchor_fact_id}")
    analysis_run_id = get_last_analysis_run_id()
    if not analysis_run_id:
        raise HumanHypothesisStoreError(
            "현재 배치 run_id 가 없습니다. 먼저 '전체 분석 시작'을 한 번 실행하세요."
        )
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )
    try:
        with driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT fact_id IF NOT EXISTS
                FOR (f:Fact) REQUIRE f.id IS UNIQUE
                """
            )
            session.run(
                """
                MERGE (f:Fact {id: $id})
                SET f.subject = $subject,
                    f.state_change = $state_change,
                    f.is_atomic = true,
                    f.timestamp = $timestamp,
                    f.trigger_event = $trigger_event,
                    f.analysis_run_id = $analysis_run_id,
                    f.source_type = $source_type,
                    f.check_status = $check_status,
                    f.reasoning = $reasoning,
                    f.anchor_fact_id = $anchor_fact_id,
                    f.author = $author,
                    f.stress_level = coalesce(f.stress_level, $stress_level),
                    f.is_critical = coalesce(f.is_critical, $is_critical)
                """,
                id=fact.id,
                subject=fact.subject,
                state_change=fact.state_change,
                timestamp=fact.timestamp.isoformat() if fact.timestamp else None,
                trigger_event=trigger_event,
                analysis_run_id=analysis_run_id,
                source_type=fact.source_type or DEFAULT_SOURCE_TYPE,
                check_status=fact.check_status or DEFAULT_CHECK_STATUS,
                reasoning=fact.reasoning or "",
                anchor_fact_id=fact.anchor_fact_id,
                author=fact.author or "human",
                stress_level=fact.stress_level or DEFAULT_STRESS_LEVEL,
                is_critical=fact.is_critical if fact.is_critical else DEFAULT_IS_CRITICAL,
            )
    finally:
        driver.close()

    _log("2", "MERGE complete")
    return fact.id
