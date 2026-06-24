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
from collections.abc import Sequence
from dataclasses import dataclass

from neo4j import GraphDatabase

from deconstructor import config
from deconstructor.provenance.types import DEFAULT_CHECK_STATUS, DEFAULT_SOURCE_TYPE
from deconstructor.storm.types import DEFAULT_IS_CRITICAL, DEFAULT_STRESS_LEVEL
from deconstructor.web.graph_context import normalize_trigger_event

logger = logging.getLogger(__name__)

# Step 2 요구: 부하 방지 상한
MAX_GRAPH_NODES = 300


@dataclass(frozen=True)
class GraphNode:
    """
    Neo4j :Fact 노드 1개 — pyvis 입력용 (provenance 포함).

    anchor_fact_id / reasoning
        Dreamer inferred 전용. anchor 는 hover 점선·툴팁 안내의 원천 id.
        reasoning 은 mechanism 문장 (Fact-Checker·Verifier 경로).
    """

    id: str
    subject: str
    state_change: str
    timestamp: str | None
    trigger_event: str | None
    source_type: str = DEFAULT_SOURCE_TYPE
    check_status: str = DEFAULT_CHECK_STATUS
    stress_level: int = DEFAULT_STRESS_LEVEL
    is_critical: bool = DEFAULT_IS_CRITICAL
    anchor_fact_id: str | None = None
    reasoning: str | None = None
    author: str | None = None
    source_file: str | None = None
    page_range: str | None = None
    chunk_id: str | None = None


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
    edge_kind: str = "CAUSES"  # CAUSES | BRIDGE (Sprint 2 cross-doc)


@dataclass(frozen=True)
class GraphFetchResult:
    """S2-5 조립 결과 + 메타 (truncated 여부)."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_limit: int
    truncated: bool
    total_nodes_in_db: int | None
    # 필터 메타 (UI·디버그)
    trigger_events_filter: tuple[str, ...] = ()
    analysis_run_id_filter: str | None = None
    matched_nodes_in_db: int | None = None


def _log(step: str, msg: str) -> None:
    """Micro-step 증명용 stdout 로그 (테스트·운영 모두 가시)."""
    line = f"[VIZ-S2-{step}] {msg}"
    logger.info(line)
    print(line)


def neo4j_is_available() -> bool:
    """Bolt 연결 가능 여부 (웹 UI fallback 판단용)."""
    if not config.NEO4J_PASSWORD:
        return False
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False
    finally:
        driver.close()


def _resolve_trigger_events_for_fetch(
    session,
    explicit: Sequence[str] | None,
) -> tuple[str, ...]:
    """
    그래프에 쓸 trigger_event 목록 (정규화).

    1. explicit 이 있으면 정규화 후 사용
    2. 없으면 DB 에서 **가장 최근** trigger_event 1건
    3. DB 비어 있으면 빈 tuple → 노드 0건
    """
    if explicit:
        return tuple(
            dict.fromkeys(
                normalize_trigger_event(te) for te in explicit if normalize_trigger_event(te)
            )
        )

    row = session.run(
        """
        MATCH (f:Fact)
        WHERE f.trigger_event IS NOT NULL AND trim(f.trigger_event) <> ""
        WITH f.trigger_event AS te, max(f.timestamp) AS latest
        ORDER BY latest DESC
        LIMIT 1
        RETURN te
        """
    ).single()
    if row and row.get("te"):
        return (normalize_trigger_event(row["te"]),)
    return ()


def _resolve_analysis_run_id_for_fetch(
    session,
    explicit: str | None,
) -> str | None:
    """명시 run_id 없으면 DB 최신 analysis_run_id 1건."""
    if explicit:
        rid = explicit.strip()
        return rid or None
    row = session.run(
        """
        MATCH (f:Fact)
        WHERE f.analysis_run_id IS NOT NULL AND trim(f.analysis_run_id) <> ""
        WITH f.analysis_run_id AS rid, max(f.timestamp) AS latest
        ORDER BY latest DESC
        LIMIT 1
        RETURN rid
        """
    ).single()
    if row and row.get("rid"):
        return str(row["rid"])
    return None


def fetch_causal_graph(
    *,
    max_nodes: int = MAX_GRAPH_NODES,
    trigger_events: Sequence[str] | None = None,
    analysis_run_id: str | None = None,
) -> GraphFetchResult:
    """
    Neo4j에서 Fact 노드(상한)와 CAUSES 엣지를 로드.

    Args:
        max_nodes: 최대 노드 수 (기본 300). 초과 시 timestamp 순 상위만.
        trigger_events: 이 원문(들)에 해당하는 fact 만 표시 (run_id 없을 때).
        analysis_run_id: 배치 UUID — **우선** 필터. 이번 분석만 표시.

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
            count_row = session.run("MATCH (f:Fact) RETURN count(f) AS c").single()
            total_in_db = int(count_row["c"]) if count_row else 0

            resolved_run_id = _resolve_analysis_run_id_for_fetch(
                session, analysis_run_id
            )
            resolved_events = _resolve_trigger_events_for_fetch(session, trigger_events)

            if resolved_run_id:
                _log(
                    "2",
                    f"filter analysis_run_id={resolved_run_id[:8]}… "
                    f"(explicit={analysis_run_id is not None})",
                )
                match_row = session.run(
                    """
                    MATCH (f:Fact)
                    WHERE f.analysis_run_id = $run_id
                    RETURN count(f) AS c
                    """,
                    run_id=resolved_run_id,
                ).single()
                matched_in_db = int(match_row["c"]) if match_row else 0
                node_query = """
                    MATCH (f:Fact)
                    WHERE f.analysis_run_id = $run_id
                    RETURN f.id AS id,
                           f.subject AS subject,
                           f.state_change AS state_change,
                           f.timestamp AS timestamp,
                           f.trigger_event AS trigger_event,
                           coalesce(f.source_type, $default_source) AS source_type,
                           coalesce(f.check_status, $default_check) AS check_status,
                           coalesce(f.stress_level, $default_stress) AS stress_level,
                           coalesce(f.is_critical, $default_critical) AS is_critical,
                           f.anchor_fact_id AS anchor_fact_id,
                           f.reasoning AS reasoning,
                           f.author AS author,
                           f.source_file AS source_file,
                           f.page_range AS page_range,
                           f.chunk_id AS chunk_id
                    ORDER BY f.timestamp, f.subject
                    LIMIT $limit
                """
                query_params = {
                    "run_id": resolved_run_id,
                    "limit": max_nodes,
                    "default_source": DEFAULT_SOURCE_TYPE,
                    "default_check": DEFAULT_CHECK_STATUS,
                    "default_stress": DEFAULT_STRESS_LEVEL,
                    "default_critical": DEFAULT_IS_CRITICAL,
                }
            elif resolved_events:
                _log(
                    "2",
                    f"filter trigger_event count={len(resolved_events)} "
                    f"preview={resolved_events[0][:48]!r}…",
                )
                match_row = session.run(
                    """
                    MATCH (f:Fact)
                    WHERE f.trigger_event IN $events
                    RETURN count(f) AS c
                    """,
                    events=list(resolved_events),
                ).single()
                matched_in_db = int(match_row["c"]) if match_row else 0
                node_query = """
                    MATCH (f:Fact)
                    WHERE f.trigger_event IN $events
                    RETURN f.id AS id,
                           f.subject AS subject,
                           f.state_change AS state_change,
                           f.timestamp AS timestamp,
                           f.trigger_event AS trigger_event,
                           coalesce(f.source_type, $default_source) AS source_type,
                           coalesce(f.check_status, $default_check) AS check_status,
                           coalesce(f.stress_level, $default_stress) AS stress_level,
                           coalesce(f.is_critical, $default_critical) AS is_critical,
                           f.anchor_fact_id AS anchor_fact_id,
                           f.reasoning AS reasoning,
                           f.author AS author,
                           f.source_file AS source_file,
                           f.page_range AS page_range,
                           f.chunk_id AS chunk_id
                    ORDER BY f.timestamp, f.subject
                    LIMIT $limit
                """
                query_params = {
                    "events": list(resolved_events),
                    "limit": max_nodes,
                    "default_source": DEFAULT_SOURCE_TYPE,
                    "default_check": DEFAULT_CHECK_STATUS,
                    "default_stress": DEFAULT_STRESS_LEVEL,
                    "default_critical": DEFAULT_IS_CRITICAL,
                }
            else:
                _log("2", "no run_id / trigger_event filter — empty graph")
                matched_in_db = 0
                node_query = None
                query_params = {}

            if not resolved_run_id and not resolved_events:
                return GraphFetchResult(
                    nodes=[],
                    edges=[],
                    node_limit=max_nodes,
                    truncated=False,
                    total_nodes_in_db=total_in_db,
                    trigger_events_filter=(),
                    analysis_run_id_filter=None,
                    matched_nodes_in_db=0,
                )

            _log(
                "2b",
                f"fetching Fact nodes filter matched={matched_in_db} "
                f"LIMIT {max_nodes} (db_total={total_in_db})",
            )
            node_rows = session.run(node_query, **query_params).data() if node_query else []

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
                    anchor_fact_id=row.get("anchor_fact_id"),
                    reasoning=row.get("reasoning") or None,
                    author=row.get("author") or None,
                    source_file=row.get("source_file") or None,
                    page_range=row.get("page_range") or None,
                    chunk_id=row.get("chunk_id") or None,
                )
                for row in node_rows
            ]
            critical_count = sum(1 for n in nodes if n.is_critical)
            if critical_count:
                from deconstructor.storm.viz_style import log_critical_nodes_fetched

                log_critical_nodes_fetched(critical_count)
            node_ids = {n.id for n in nodes}
            truncated = matched_in_db > len(nodes)

            _log(
                "3",
                f"nodes loaded={len(nodes)} truncated={truncated} "
                f"(matched_in_db={matched_in_db})",
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
                trigger_events_filter=resolved_events,
                analysis_run_id_filter=resolved_run_id,
                matched_nodes_in_db=matched_in_db,
            )
    finally:
        driver.close()
        _log("1", "driver closed")
