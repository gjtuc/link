"""
마지막 배치 파이프라인 — 디버그 스냅샷 (파란·노랑 누락 조사)
============================================================

STAGE 0-3 (Acceptance) — 관측 proxy
------------------------------------
  - AC-DBG-01: ``build_pipeline_debug`` — completed, orphan, fact_checker_mode
  - AC-DEC-02 proxy: ``counts.completed_facts`` per run
  - AC-SKP-03/04 proxy (partial): orphan_extracted, endpoint_facts (until skeleton index)

Sprint 1 (G-ING-META)
---------------------
  - AC-ING-05: ``_fact_brief`` source_file/chunk_id; ``source_document_meta`` per run

Sprint 3 (G-DEC-DENS/RECUR)
---------------------------
  - AC-DEC-02 proxy: ``deconstruct_batch.median_completed_facts``
  - AC-DEC-03: ``deconstruct_batch.runs_with_depth_gt_1``

  See ``docs/design/STAGE-0-3-acceptance-criteria.md``
"""

from __future__ import annotations

from typing import Any

from deconstructor.models import AtomicFact
from deconstructor.viz.neo4j_utils import GraphFetchResult, neo4j_is_available
from deconstructor.weaver.resolve import facts_for_verified_edges, orphan_atomic_completed_facts


def _median_int(values: list[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _fact_brief(fact: AtomicFact) -> dict[str, str]:
    out = {
        "id": fact.id[:16],
        "subject": (fact.subject or "")[:100],
        "state_change": (fact.state_change or "")[:60],
        "source_type": fact.source_type or "?",
        "check_status": fact.check_status or "?",
        "is_atomic": str(bool(fact.is_atomic)),
    }
    if fact.source_file:
        out["source_file"] = fact.source_file[:120]
    if fact.page_range:
        out["page_range"] = fact.page_range[:40]
    if fact.chunk_id:
        out["chunk_id"] = fact.chunk_id[:120]
    return out


def _count_by_legend(nodes: list) -> dict[str, int]:
    """GraphNode 목록 → 범례 색 카운트."""
    from deconstructor.provenance.types import is_ghost_dropped, is_promoted_inferred

    counts = {
        "extracted_blue": 0,
        "verified_green": 0,
        "inferred_pending_yellow": 0,
        "promoted_yellow_green": 0,
        "dropped_brown": 0,
        "other": 0,
    }
    for n in nodes:
        st = n.source_type or ""
        cs = n.check_status or ""
        if is_ghost_dropped(st, cs):
            counts["dropped_brown"] += 1
        elif is_promoted_inferred(st, cs):
            counts["promoted_yellow_green"] += 1
        elif st == "inferred" and cs == "pending":
            counts["inferred_pending_yellow"] += 1
        elif st == "verified":
            counts["verified_green"] += 1
        elif st == "extracted":
            counts["extracted_blue"] += 1
        else:
            counts["other"] += 1
    return counts


def summarize_single_state(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph state 1건 — Weaver가 뭘 저장해야 하는지."""
    completed = list(state.get("completed_facts") or [])
    promoted = list(state.get("promoted_facts") or [])
    dropped = list(state.get("dropped_hypotheses") or [])
    edges = list(state.get("verified_edges") or [])
    all_pool = completed + promoted

    endpoint_facts = facts_for_verified_edges(all_pool, edges)
    endpoint_ids = {f.id for f in endpoint_facts}
    ghost_facts = [d.ghost_fact for d in dropped]
    orphan_promoted = [f for f in promoted if f.id not in endpoint_ids]
    orphan_extracted = orphan_atomic_completed_facts(
        completed,
        already_persisted_ids=endpoint_ids
        | {f.id for f in orphan_promoted}
        | {f.id for f in ghost_facts},
    )

    return {
        "analysis_run_id": state.get("analysis_run_id"),
        "raw_text_preview": (state.get("raw_text") or "")[:200],
        "source_document_meta": dict(state.get("source_document_meta") or {}),
        "deconstruct": {
            "recursion_depth": int(state.get("recursion_depth") or 0),
            "max_recursion_depth": int(state.get("max_recursion_depth") or 0),
            "partial_run": bool(state.get("partial_run")),
            "partial_run_reason": str(state.get("partial_run_reason") or ""),
        },
        "counts": {
            "completed_facts": len(completed),
            "promoted_facts": len(promoted),
            "dropped_ghosts": len(dropped),
            "verified_edges": len(edges),
        },
        "weaver_would_persist": {
            "endpoint_facts": len(endpoint_facts),
            "orphan_extracted": len(orphan_extracted),
            "orphan_promoted": len(orphan_promoted),
            "ghost_facts": len(ghost_facts),
        },
        "samples": {
            "completed_facts": [_fact_brief(f) for f in completed[:15]],
            "orphan_extracted": [_fact_brief(f) for f in orphan_extracted[:15]],
            "promoted_facts": [_fact_brief(f) for f in promoted[:15]],
            "dropped_ghosts": [_fact_brief(d.ghost_fact) for d in dropped[:15]],
            "endpoint_facts": [_fact_brief(f) for f in endpoint_facts[:15]],
        },
        "diagnosis": _diagnose_state(
            len(completed), len(orphan_extracted), len(promoted), len(dropped), len(edges)
        ),
    }


def _diagnose_state(
    completed_n: int,
    orphan_extracted_n: int,
    promoted_n: int,
    dropped_n: int,
    edges_n: int,
) -> list[str]:
    hints: list[str] = []
    if completed_n == 0:
        hints.append(
            "completed_facts=0 → Deconstruct/Verify가 원자 사실을 못 뽑음. "
            "파란 노드 불가 (입력·Gemini·깊이 상한 확인)."
        )
    elif orphan_extracted_n == 0 and edges_n == 0:
        hints.append(
            "completed는 있으나 orphan_extracted=0 이고 엣지=0 — "
            "completed가 endpoint_ids에 이미 포함됐거나 is_atomic=False일 수 있음."
        )
    elif orphan_extracted_n > 0:
        hints.append(
            f"orphan_extracted={orphan_extracted_n} → Weaver가 파란 노드로 저장해야 함. "
            "그래프에 없으면 서버 재시작·재분석 또는 Neo4j MERGE 확인."
        )
    if promoted_n == 0 and dropped_n > 0:
        hints.append(
            "promoted=0, dropped>0 → Fact-Checker가 가설 전부 기각. "
            "노랑+초록 없음은 정상에 가까움 (Tavily live면 엄격)."
        )
    if edges_n == 0:
        hints.append("verified_edges=0 → Skeptic 인과 연결 없음. 선(엣지) 없이 노드만 표시됨.")
    return hints


def query_neo4j_run_breakdown(analysis_run_id: str | None) -> dict[str, Any]:
    """Neo4j — run_id별 source_type/check_status 집계 + 샘플."""
    if not analysis_run_id:
        return {"available": False, "reason": "analysis_run_id 없음"}
    if not neo4j_is_available():
        return {"available": False, "reason": "Neo4j bolt 불가"}

    from neo4j import GraphDatabase

    from deconstructor import config

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )
    try:
        with driver.session() as session:
            total = session.run("MATCH (f:Fact) RETURN count(f) AS c").single()
            matched = session.run(
                """
                MATCH (f:Fact)
                WHERE f.analysis_run_id = $rid
                RETURN count(f) AS c
                """,
                rid=analysis_run_id,
            ).single()
            by_type = session.run(
                """
                MATCH (f:Fact)
                WHERE f.analysis_run_id = $rid
                RETURN coalesce(f.source_type, '?') AS st,
                       coalesce(f.check_status, '?') AS cs,
                       count(*) AS c
                ORDER BY c DESC
                """,
                rid=analysis_run_id,
            ).data()
            samples = session.run(
                """
                MATCH (f:Fact)
                WHERE f.analysis_run_id = $rid
                RETURN f.id AS id, f.subject AS subject,
                       f.source_type AS source_type,
                       f.check_status AS check_status
                ORDER BY f.timestamp, f.subject
                LIMIT 30
                """,
                rid=analysis_run_id,
            ).data()
            legacy_no_run = session.run(
                """
                MATCH (f:Fact)
                WHERE f.analysis_run_id IS NULL OR trim(f.analysis_run_id) = ''
                RETURN count(f) AS c
                """
            ).single()
        return {
            "available": True,
            "analysis_run_id": analysis_run_id,
            "db_total_facts": int(total["c"]) if total else 0,
            "run_matched_facts": int(matched["c"]) if matched else 0,
            "legacy_facts_without_run_id": int(legacy_no_run["c"]) if legacy_no_run else 0,
            "by_source_and_status": by_type,
            "samples": samples,
        }
    finally:
        driver.close()


def build_pipeline_debug(
    pipeline_states: list[dict[str, Any]],
    *,
    fetched: GraphFetchResult,
    batch_run_id: str,
    fact_checker_mode: str,
) -> dict[str, Any]:
    """배치 1회 전체 디버그 페이로드."""
    runs = [summarize_single_state(s) for s in pipeline_states]
    graph_counts = _count_by_legend(fetched.nodes)
    neo4j = query_neo4j_run_breakdown(batch_run_id)
    completed_per_run = [r["counts"]["completed_facts"] for r in runs]
    depths = [r["deconstruct"]["recursion_depth"] for r in runs]
    partial_runs = [
        {
            "run_index": i + 1,
            "reason": r["deconstruct"]["partial_run_reason"],
            "source_file": (r.get("source_document_meta") or {}).get("source_file", ""),
        }
        for i, r in enumerate(runs)
        if r["deconstruct"].get("partial_run")
    ]
    median_completed = _median_int(completed_per_run)

    return {
        "batch_run_id": batch_run_id,
        "fact_checker_mode": fact_checker_mode,
        "deconstruct_batch": {
            "runs": len(runs),
            "completed_facts_per_run": completed_per_run,
            "median_completed_facts": median_completed,
            "recursion_depths": depths,
            "runs_with_depth_gt_1": sum(1 for d in depths if d > 1),
            "partial_run_runs": partial_runs,
            "partial_run_count": len(partial_runs),
            "max_recursion_depth": max(
                (r["deconstruct"]["max_recursion_depth"] for r in runs), default=0
            ),
        },
        "pipeline_runs": runs,
        "graph_rendered": {
            "nodes": len(fetched.nodes),
            "edges": len(fetched.edges),
            "legend_counts": graph_counts,
            "node_samples": [
                {
                    "id": n.id[:16],
                    "subject": (n.subject or "")[:80],
                    "source_type": n.source_type,
                    "check_status": n.check_status,
                }
                for n in fetched.nodes[:25]
            ],
        },
        "neo4j": neo4j,
        "top_diagnosis": _merge_diagnosis(runs, graph_counts, neo4j),
    }


def _merge_diagnosis(
    runs: list[dict],
    graph_counts: dict[str, int],
    neo4j: dict,
) -> list[str]:
    hints: list[str] = []
    for r in runs:
        hints.extend(r.get("diagnosis") or [])
        if r["deconstruct"].get("partial_run"):
            hints.append(
                "partial_run=True — "
                f"{r['deconstruct'].get('partial_run_reason', '')}: "
                "비원자 crumb 잔존 (깊이 상한). 메인 UI watch 패널 확인."
            )

    blue_graph = graph_counts.get("extracted_blue", 0)
    blue_neo4j = sum(
        row["c"]
        for row in (neo4j.get("by_source_and_status") or [])
        if row.get("st") == "extracted"
    )
    if blue_graph == 0 and blue_neo4j == 0:
        total_completed = sum(r["counts"]["completed_facts"] for r in runs)
        if total_completed > 0:
            hints.append(
                f"파이프라인 completed_facts={total_completed} 인데 "
                "그래프·Neo4j 모두 extracted=0 → Weaver 저장 버그 또는 서버 구버전."
            )
    elif blue_neo4j > 0 and blue_graph == 0:
        hints.append(
            f"Neo4j에 extracted {blue_neo4j}건 있으나 그래프 렌더 0 → "
            "graph_filter·fetch_causal_graph·HTML 캐시 확인."
        )
    return list(dict.fromkeys(hints))
