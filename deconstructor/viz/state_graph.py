"""
파이프라인 State → pyvis 입력 (Neo4j 없이 로컬 미리보기)
========================================================

Purpose / 목적
--------------
Neo4j가 꺼져 있거나 웹 UI가 **이번 세션 결과만** 그릴 때,
LangGraph ``State`` dict 를 ``GraphNode`` / ``GraphEdge`` 로 변환한다.

Pipeline position / 파이프라인 위치
---------------------------------
  run_pipeline → state
  → **graph_from_pipeline_state** (Neo4j offline)
  → visualizer.render_to_html

  Neo4j online 시에는 ``neo4j_utils.fetch_causal_graph`` 가 DB 누적 그래프를 쓰고,
  이 모듈은 **세션 전용** fallback.

노드 수집 순서 (단계)
--------------------
  1. ``verified_edges`` 양 끝 + ``completed_facts`` / ``promoted_facts`` 풀
  2. ``facts_for_verified_edges`` — Skeptic 통과 엔드포인트만 (기본)
  3. **orphan extracted** — CAUSES 없어도 completed 원자(파랑) 표시
  4. **orphan promoted** — 엣지 없는 Fact-Checker 통과 가설도 포함
  5. **dropped ghosts** — 기각 가설(흐린 노랑) 시각화
  6. **anchor 보강** — inferred 의 ``anchor_fact_id`` 원천이 (5)까지 빠졌으면
     completed 풀에서 끌어와 hover 점선·툴팁용 파랑 노드 확보

When to modify / 수정 시점
--------------------------
- orphan·ghost 포함 정책 변경 시 weaver/node.py 와 동기화
- ``GraphNode`` 필드 추가 시 ``_fact_to_node`` · neo4j MERGE · visualizer 동시 갱신

Sprint 2 (G-ORC-POLICY)
-----------------------
  - ``merge_graph_results``: node id dedup, later wins (POL-03)
  - Cross-doc BRIDGE edges: ``web/corpus_bridge.attach_bridge_edges`` (post-merge)
  - See ``docs/design/SPRINT-2-orchestration-spec.md``
"""

from __future__ import annotations

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.viz.neo4j_utils import GraphEdge, GraphFetchResult, GraphNode
from deconstructor.weaver.resolve import (
    facts_for_verified_edges,
    orphan_atomic_completed_facts,
)


def _fact_to_node(fact: AtomicFact, trigger_event: str) -> GraphNode:
    """AtomicFact → pyvis용 GraphNode (provenance·anchor·reasoning 포함)."""
    ts = fact.timestamp.isoformat() if fact.timestamp else None
    return GraphNode(
        id=fact.id,
        subject=fact.subject,
        state_change=fact.state_change,
        timestamp=ts,
        trigger_event=trigger_event,
        source_type=fact.source_type,
        check_status=fact.check_status,
        stress_level=fact.stress_level,
        is_critical=fact.is_critical,
        anchor_fact_id=fact.anchor_fact_id,
        reasoning=fact.reasoning or None,
        source_file=fact.source_file or None,
        page_range=fact.page_range or None,
        chunk_id=fact.chunk_id or None,
    )


def _edge_to_graph(edge: CausalEdge) -> GraphEdge:
    """Skeptic 검증 CAUSES → pyvis directed edge."""
    return GraphEdge(
        source_id=edge.source_fact_id,
        target_id=edge.target_fact_id,
        probability=edge.probability,
        latency=edge.latency,
        edge_kind="CAUSES",
    )


def graph_from_pipeline_state(state: dict) -> GraphFetchResult:
    """
    단일 파이프라인 실행 결과를 그래프 데이터로 변환.

    Step A — 엣지·엔드포인트 fact
    Step B — promoted orphan / dropped ghost 추가
    Step C — Dreamer anchor 원천 fact 보강 (hover 점선 대상)
    """
    edges = state.get("verified_edges") or []
    all_facts = list(state.get("completed_facts") or []) + list(
        state.get("promoted_facts") or []
    )
    facts = facts_for_verified_edges(all_facts, edges)
    seen_ids = {f.id for f in facts}
    for fact in state.get("promoted_facts") or []:
        if fact.id not in seen_ids:
            facts.append(fact)
            seen_ids.add(fact.id)
    for fact in orphan_atomic_completed_facts(
        state.get("completed_facts") or [],
        already_persisted_ids=seen_ids,
    ):
        facts.append(fact)
        seen_ids.add(fact.id)
    for dropped in state.get("dropped_hypotheses") or []:
        ghost = dropped.ghost_fact
        if ghost.id not in seen_ids:
            facts.append(ghost)
            seen_ids.add(ghost.id)

    # Step C: inferred anchor → 원천 파랑 노드 (그래프에 없으면 hover 점선 불가)
    all_by_id = {f.id: f for f in all_facts}
    for fact in list(facts):
        anchor_id = fact.anchor_fact_id
        if anchor_id and anchor_id not in seen_ids:
            anchor = all_by_id.get(anchor_id)
            if anchor is not None:
                facts.append(anchor)
                seen_ids.add(anchor.id)

    trigger = state.get("raw_text") or ""

    nodes = [_fact_to_node(f, trigger) for f in facts]
    graph_edges = [_edge_to_graph(e) for e in edges]
    return GraphFetchResult(
        nodes=nodes,
        edges=graph_edges,
        node_limit=len(nodes),
        truncated=False,
        total_nodes_in_db=None,
    )


def merge_graph_results(results: list[GraphFetchResult]) -> GraphFetchResult:
    """여러 배치 실행 결과를 노드 id 기준으로 병합 (웹 UI 다건 분석).

    POL-03: 동일 node id → **나중 run wins** (UUID collision rare).
    CAUSES edges dedup by (source_id, target_id). BRIDGE edges added separately.
    """
    node_map: dict[str, GraphNode] = {}
    edge_keys: set[tuple[str, str]] = set()
    merged_edges: list[GraphEdge] = []

    for result in results:
        for node in result.nodes:
            node_map[node.id] = node
        for edge in result.edges:
            key = (edge.source_id, edge.target_id)
            if key not in edge_keys:
                edge_keys.add(key)
                merged_edges.append(edge)

    nodes = list(node_map.values())
    return GraphFetchResult(
        nodes=nodes,
        edges=merged_edges,
        node_limit=len(nodes),
        truncated=False,
        total_nodes_in_db=None,
    )
