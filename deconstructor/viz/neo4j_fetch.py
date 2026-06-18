"""
Neo4j 시각화 — DB 전체 그래프 조회
==================================

## 역할

파이프라인 `--db` 종료 후 viz.export 가 호출하여
**DB에 있는 모든** :Fact 노드와 :CAUSES 관계를 읽어 pyvis 입력으로 변환.

## 스키마 (weaver/neo4j_store.py 와 일치해야 함)

  (:Fact {id, subject, state_change, timestamp, trigger_event, is_atomic})
  (:Fact)-[:CAUSES {probability, latency}]->(:Fact)

## 다른 AI가 수정할 때

  - Weaver가 다른 라벨/관계명 쓰면 MATCH 쿼리도 같이 변경
  - 누적 실행 시 이전 run 노드도 포함됨 (의도된 동작 — DB 전체 스냅샷)
  - config.NEO4J_* 로 연결 (local_settings.py 우선)
"""

from __future__ import annotations

from dataclasses import dataclass

from neo4j import GraphDatabase

from deconstructor import config


@dataclass(frozen=True)
class GraphNode:
    """pyvis 노드 1개분. Neo4j Fact 속성의 읽기 전용 뷰."""

    id: str
    subject: str
    state_change: str
    timestamp: str | None
    trigger_event: str | None


@dataclass(frozen=True)
class GraphEdge:
    """pyvis directed edge 1개분."""

    source_id: str
    target_id: str
    probability: float
    latency: int | None


def fetch_full_graph() -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Neo4j에서 모든 Fact·CAUSES 를 로드.

    Returns:
        (nodes, edges) — 빈 DB면 ([], [])

  Raises:
        neo4j 예외 (연결 실패 등) — export.maybe_visualize_after_pipeline 이 catch.

    수정 시:
        ORDER BY 로 시각적 안정성 확보; timestamp null 은 정렬 맨 앞/뒤로 감.
    """
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )
    try:
        with driver.session() as session:
            # 전체 Fact 노드 (실행마다 MERGE 되므로 누적 가능)
            node_rows = session.run(
                """
                MATCH (f:Fact)
                RETURN f.id AS id,
                       f.subject AS subject,
                       f.state_change AS state_change,
                       f.timestamp AS timestamp,
                       f.trigger_event AS trigger_event
                ORDER BY f.timestamp, f.subject
                """
            ).data()
            edge_rows = session.run(
                """
                MATCH (a:Fact)-[r:CAUSES]->(b:Fact)
                RETURN a.id AS source_id,
                       b.id AS target_id,
                       r.probability AS probability,
                       r.latency AS latency
                """
            ).data()
    finally:
        driver.close()

    nodes = [
        GraphNode(
            id=row["id"],
            subject=row["subject"] or "",
            state_change=row["state_change"] or "",
            timestamp=row["timestamp"],
            trigger_event=row["trigger_event"],
        )
        for row in node_rows
    ]
    edges = [
        GraphEdge(
            source_id=row["source_id"],
            target_id=row["target_id"],
            probability=float(row["probability"] or 0),
            latency=row["latency"],
        )
        for row in edge_rows
    ]
    return nodes, edges
