"""
Step 2 — Neo4j → Python 데이터 추출 (Micro-step)
=================================================

목적:
  Weaver가 MERGE 한 **검증된 인과(:CAUSES)** 만 Neo4j에 존재한다.
  Rejected 상관관계는 DB에 저장되지 않으므로, 여기서 읽는 엣지 = 인과만.

Micro-steps (각 단계마다 [VIZ-S2-...] 로그):
  S2-1  드라이버 연결
  S2-2  Fact 노드 조회 (LIMIT max_nodes)
  S2-3  노드 수·truncated 여부 기록
  S2-4  CAUSES 엣지 조회 (양 끝이 S2-2 노드 집합에 포함된 것만)
  S2-5  결과 조립 및 반환

수정 시:
  weaver/neo4j_store.py 스키마와 MATCH 라벨/속성명 일치 필수.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from neo4j import GraphDatabase

from deconstructor import config
from deconstructor.provenance.types import DEFAULT_CHECK_STATUS, DEFAULT_SOURCE_TYPE
from deconstructor.storm.types import DEFAULT_IS_CRITICAL, DEFAULT_STRESS_LEVEL

logger = logging.getLogger(__name__)

# Step 2 요구: 부하 방지 상한
MAX_GRAPH_NODES = 300


@dataclass(frozen=True)
class GraphNode:
    """Neo4j :Fact 노드 1개 — pyvis 입력용 (provenance 포함)."""

    id: str
    subject: str
    state_change: str
    timestamp: str | None
    trigger_event: str | None
    source_type: str = DEFAULT_SOURCE_TYPE
    check_status: str = DEFAULT_CHECK_STATUS
    stress_level: int = DEFAULT_STRESS_LEVEL
    is_critical: bool = DEFAULT_IS_CRITICAL


@dataclass(frozen=True)
class GraphEdge:
    """
    Neo4j :CAUSES 관계 1개 — Skeptic 검증 통과분만 DB에 존재.

    Rejected correlation 은 Neo4j에 기록되지 않으므로 이 타입으로
    시각화되는 선 = 인과만 (Step 3에서 추가 필터 불필요).
    """

    source_id: str
    target_id: str
    probability: float
    latency: int | None


@dataclass(frozen=True)
class GraphFetchResult:
    """S2-5 조립 결과 + 메타 (truncated 여부)."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_limit: int
    truncated: bool
    total_nodes_in_db: int | None


def _log(step: str, msg: str) -> None:
    """Micro-step 증명용 stdout 로그 (테스트·운영 모두 가시)."""
    line = f"[VIZ-S2-{step}] {msg}"
    logger.info(line)
    print(line)


def fetch_causal_graph(
    *,
    max_nodes: int = MAX_GRAPH_NODES,
) -> GraphFetchResult:
    """
    Neo4j에서 Fact 노드(상한)와 CAUSES 엣지를 로드.

    Args:
        max_nodes: 최대 노드 수 (기본 300). 초과 시 timestamp 순 상위만.

    Returns:
        GraphFetchResult — nodes, edges, truncated 플래그 포함.

    Raises:
        neo4j 예외 — 연결/인증 실패 시 export 단계에서 catch.
    """
    if max_nodes < 1:
        raise ValueError("max_nodes must be >= 1")

    _log("1", f"connecting Neo4j uri={config.NEO4J_URI}")
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )

    try:
        with driver.session() as session:
            # S2-2: 전체 노드 수 (truncated 판단용, 가벼운 count)
            count_row = session.run("MATCH (f:Fact) RETURN count(f) AS c").single()
            total_in_db = int(count_row["c"]) if count_row else 0

            _log(
                "2",
                f"fetching Fact nodes (+ source_type, check_status, stress_level, is_critical) "
                f"LIMIT {max_nodes} (db_total={total_in_db})",
            )
            node_rows = session.run(
                """
                MATCH (f:Fact)
                RETURN f.id AS id,
                       f.subject AS subject,
                       f.state_change AS state_change,
                       f.timestamp AS timestamp,
                       f.trigger_event AS trigger_event,
                       coalesce(f.source_type, $default_source) AS source_type,
                       coalesce(f.check_status, $default_check) AS check_status,
                       coalesce(f.stress_level, $default_stress) AS stress_level,
                       coalesce(f.is_critical, $default_critical) AS is_critical
                ORDER BY f.timestamp, f.subject
                LIMIT $limit
                """,
                limit=max_nodes,
                default_source=DEFAULT_SOURCE_TYPE,
                default_check=DEFAULT_CHECK_STATUS,
                default_stress=DEFAULT_STRESS_LEVEL,
                default_critical=DEFAULT_IS_CRITICAL,
            ).data()

            nodes = [
                GraphNode(
                    id=row["id"],
                    subject=row["subject"] or "",
                    state_change=row["state_change"] or "",
                    timestamp=row["timestamp"],
                    trigger_event=row["trigger_event"],
                    source_type=row["source_type"] or DEFAULT_SOURCE_TYPE,
                    check_status=row["check_status"] or DEFAULT_CHECK_STATUS,
                    stress_level=int(row["stress_level"] or DEFAULT_STRESS_LEVEL),
                    is_critical=bool(row["is_critical"]),
                )
                for row in node_rows
            ]
            critical_count = sum(1 for n in nodes if n.is_critical)
            if critical_count:
                from deconstructor.storm.viz_style import log_critical_nodes_fetched

                log_critical_nodes_fetched(critical_count)
            node_ids = {n.id for n in nodes}
            truncated = total_in_db > len(nodes)

            _log(
                "3",
                f"nodes loaded={len(nodes)} truncated={truncated}",
            )

            if not node_ids:
                _log("4", "no nodes — skipping edge query")
                edges: list[GraphEdge] = []
            else:
                _log(
                    "4",
                    f"fetching CAUSES edges where both endpoints in {len(node_ids)} nodes",
                )
                edge_rows = session.run(
                    """
                    MATCH (a:Fact)-[r:CAUSES]->(b:Fact)
                    WHERE a.id IN $ids AND b.id IN $ids
                    RETURN a.id AS source_id,
                           b.id AS target_id,
                           r.probability AS probability,
                           r.latency AS latency
                    """,
                    ids=list(node_ids),
                ).data()
                edges = [
                    GraphEdge(
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        probability=float(row["probability"] or 0),
                        latency=row["latency"],
                    )
                    for row in edge_rows
                ]
                _log("4", f"verified CAUSES edges loaded={len(edges)} (rejected not in DB)")

            _log("5", f"assemble complete nodes={len(nodes)} edges={len(edges)}")
            return GraphFetchResult(
                nodes=nodes,
                edges=edges,
                node_limit=max_nodes,
                truncated=truncated,
                total_nodes_in_db=total_in_db,
            )
    finally:
        driver.close()
        _log("1", "driver closed")
