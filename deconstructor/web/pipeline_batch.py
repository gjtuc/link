"""
Link UI — 배치 분석 오케스트레이션 (세분화 단계 추적)

STAGE 0-1 (제품 계약) — Orchestration (현재: silo, 2단계에서 corpus화)
-----------------------------------------------------------------------
  - 한 번 「전체 분석」= 완성품(소스) N건 → 파이프라인 N회 → 그래프 병합.
  - **0-1 목표**: 각 소스에서 因·과 지도·뼈대 강약을 **숨기지 않고** 표시 (δ).
  - **0-1 NON-GOAL**: 파일 간 「뜻밖의 연결」 (2단계). 현재 ``merge_graph_results`` 는
    노드 id 합치기만 (NG-2: 노드 많음 ≠ 성공).
  - **0-2 시나리오**: S0-A PDF 1편, S0-B 텍스트 초안, S0-C 다중 파일(P1 gap), S0-D URL.
    See ``docs/design/STAGE-0-2-user-scenarios.md``.
  - 상세: ``docs/design/STAGE-0-1-product-definition.md`` (α-4, ζ, C-3)

STAGE 0-5 (Roadmap) — Orchestration
------------------------------------
  - Sprint 1 ✅: SP1-META-* — ``source_document_meta`` per source (AC-ING-05)
  - Sprint 2: SP2-BRG-* — ``corpus_bridge.attach_bridge_edges`` (AC-ORC-02)
  - See ``docs/design/SPRINT-2-orchestration-spec.md``
  - Sprint 2: SP2-BRG-*, SP2-POL-* — G-ORC-BRIDGE (D-05: policy first)
  - Sprint 4 ✅: SP4-IDX-*, SP4-UI-* — skeleton index + Health/Outline UI (AC-SKP-03~05, UI-04,05)
  - Sprint 5 ✅: SP5-* — corpus Fact-Checker (AC-FC-02 full, G-FC-CORPUS)
  - Sprint 6 ✅: SP6-* — post-pipeline recompose ε-2~4 (AC-REC-02)
  - Sprint 7 ✅: SP7-* — watch/guards (AC-DEC-04, ING-07, SKP-05)
  - See ``docs/design/SPRINT-4-skeleton-ui-spec.md`` … ``SPRINT-7-watch-spec.md``

INGEST Foundation (Phase R → A)
-------------------------------
  - **Phase R (읽기 확인):** ``verify_read`` — LLM 0회, step ``S1-READ``
  - **Phase A (분석 확인):** Deconstruct+ — ``read_verify.ok`` 후만 실행
  - See ``docs/design/INGEST-FOUNDATION-spec.md``

μ-PROBE-S5 — Neo4j auto-start skip (probe·배치 공통)
---------------------------------------------------
  - **env:** ``LINK_DISABLE_NEO4J_AUTO_START=1`` (또는 ``true``/``yes``)
  - **효과:** ``_ensure_neo4j_tracked`` 가 S5 ``ensure_neo4j_running``·90s 대기·Desktop
    기동을 **건너뜀** — tracker ``S5-NEO4J-ENSURE`` skip
  - **용도:** ``capability_catalog_probe.py neo4j-off`` (bolt 불가 시 세션 그래프만)
  - **스펙:** ``docs/design/CAPABILITY-PROBE-spec.md`` § LINK_DISABLE_NEO4J_AUTO_START
  - **검증:** ``tests/test_pipeline_neo4j_probe_skip.py``

STAGE-1 (μ-2b-01) — cross-run corpus ingest
-------------------------------------------
  - **env:** ``LINK_CROSS_RUN_CORPUS=1`` (기본 off)
  - **hook:** ``corpus.ingest_hook.maybe_append_batch_corpus`` (성공 후 side-effect)
  - **스펙:** ``docs/design/STAGE-1-CORPUS-spec.md``

진행 규칙: ``docs/design/PROCESS.md``
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from deconstructor.web.extract import ExtractedSource
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.graph_context import set_last_graph_filter
from deconstructor.web.pipeline_link import run_pipeline_with_steps

ROOT = Path(__file__).resolve().parents[2]
GRAPH_HTML = ROOT / "graph_output.html"


def run_pipeline_batch(
    sources: list[ExtractedSource],
    tracker: LinkStepTracker | None = None,
) -> dict:
    """추출된 소스 → 파이프라인 → Neo4j → 그래프 HTML. 실패 시 ``failed_step``·``steps`` 포함."""
    tr = tracker or LinkStepTracker()
    try:
        return _run_pipeline_batch_inner(sources, tr)
    except Exception as exc:
        return tr.fail(exc)


def _ensure_neo4j_tracked(tracker: LinkStepTracker, pipeline_states: list) -> tuple[bool, dict | None]:
    if os.getenv("LINK_DISABLE_NEO4J_AUTO_START", "").lower() in ("1", "true", "yes"):
        tracker.skip("S5-NEO4J-ENSURE", "auto-start disabled (probe)")
        return False, {
            "attempted": False,
            "available": False,
            "method": "disabled",
            "message": "LINK_DISABLE_NEO4J_AUTO_START",
        }

    from deconstructor.neo4j_launcher import (
        ensure_neo4j_running,
        persist_state_to_neo4j,
        probe_neo4j_installation,
    )
    from deconstructor.viz.neo4j_utils import neo4j_is_available

    if neo4j_is_available():
        tracker.skip("S5-NEO4J-ENSURE", "이미 bolt 연결됨")
        return True, None

    tracker.start("S5-NEO4J-PROBE", "Neo4j 설치 경로 탐색")
    probe = probe_neo4j_installation(ROOT)
    if not probe.any_installed:
        tracker.skip("S5-NEO4J-PROBE", "미설치")
        return False, {
            "attempted": False,
            "available": False,
            "method": "none",
            "message": "Neo4j/Docker 미설치",
        }
    parts = []
    if probe.docker_cli:
        parts.append("docker")
    if probe.desktop_exe:
        parts.append("desktop")
    tracker.ok("S5-NEO4J-PROBE", ", ".join(parts) or "found")

    tracker.start("S5-NEO4J-START", "Neo4j 기동·bolt 대기", "최대 90초")
    ensure = ensure_neo4j_running(ROOT, wait_timeout_sec=90)
    neo4j_sync = {
        "attempted": True,
        "available": ensure.available,
        "method": ensure.method,
        "message": ensure.message,
        "waited_sec": round(ensure.waited_sec, 1),
    }
    if ensure.available:
        tracker.ok("S5-NEO4J-START", f"{ensure.method} ({ensure.waited_sec:.0f}s)")
        for i, state in enumerate(pipeline_states, start=1):
            bf = f"S5-NEO4J-BACKFILL-{i}"
            tracker.start(bf, f"Neo4j 백필 {i}/{len(pipeline_states)}", "weaver persist")
            persist_state_to_neo4j(state)
            tracker.ok(bf)
        return True, neo4j_sync

    tracker.skip("S5-NEO4J-START", "기동 실패", ensure.message[:120])
    return False, neo4j_sync


def _render_graph_tracked(tracker: LinkStepTracker, nodes, edges) -> None:
    from deconstructor.viz.visualizer import build_pyvis_network, inject_legend_into_html

    tracker.start("S7-RENDER-NET", "pyvis 네트워크 생성", f"nodes={len(nodes)}")
    net = build_pyvis_network(nodes, edges, title="Deconstructor Causal Graph")
    tracker.ok("S7-RENDER-NET")

    tracker.start("S7-RENDER-SAVE", "HTML 파일 저장", GRAPH_HTML.name)
    output_path = GRAPH_HTML.resolve()
    net.save_graph(str(output_path))
    tracker.ok("S7-RENDER-SAVE")

    tracker.start("S7-RENDER-LEGEND", "범례·hover JS 주입")
    inject_legend_into_html(output_path)
    tracker.ok("S7-RENDER-LEGEND")


def _run_pipeline_batch_inner(sources: list[ExtractedSource], tracker: LinkStepTracker) -> dict:
    from deconstructor import config
    from deconstructor.report import format_dry_run_report
    from deconstructor.viz.neo4j_utils import fetch_causal_graph, neo4j_is_available
    from deconstructor.viz.state_graph import graph_from_pipeline_state, merge_graph_results

    tracker.start("S1-INPUT", "입력 검증", f"{len(sources)}건")
    if not sources:
        raise ValueError("분석할 소스가 없습니다")
    tracker.ok("S1-INPUT")

    from deconstructor.web.ingest_verify import verify_read

    tracker.start("S1-READ", "읽기 확인 (Phase R, μ-R-*)")
    read_report = verify_read(sources)
    if read_report.blocking or not read_report.ok:
        fail_payload = tracker.fail(
            ValueError(read_report.message or "읽기 확인 실패 — 분석(Phase A) 중단"),
            step="S1-READ",
        )
        fail_payload["read_verify"] = read_report.to_dict()
        if read_report.blocking:
            from deconstructor.guards import check_f0_a2_blocking

            fail_payload["watch"] = check_f0_a2_blocking(sources).to_watch_dict()
        return fail_payload
    passed = read_report.to_dict()["passed"]
    total = read_report.to_dict()["total"]
    tracker.ok("S1-READ", f"{passed}/{total} checks")
    read_verify_payload = read_report.to_dict()

    batch_run_id = str(uuid.uuid4())
    batch_trigger_events = [src.text for src in sources]
    set_last_graph_filter(
        analysis_run_id=batch_run_id,
        trigger_events=batch_trigger_events,
    )

    tracker.start("S3-NEO4J-BOLT", "Neo4j bolt 핑")
    use_db = neo4j_is_available()
    tracker.ok("S3-NEO4J-BOLT", "연결됨" if use_db else "오프라인")

    has_tavily = config.tavily_enabled()
    fc_mode = config.resolve_fact_checker_mode()
    tracker.start("S3-CONFIG-TAVILY", "Fact-Checker", fc_mode)
    tracker.ok("S3-CONFIG-TAVILY")

    tracker.start("S3-CONFIG-GEMINI", "LLM (Deconstruct·Dreamer)")
    tracker.ok("S3-CONFIG-GEMINI", "Gemini API")

    neo4j_sync: dict | None = None
    runs: list[dict] = []
    session_graphs: list = []
    pipeline_states: list = []

    corpus_pool_accum: list = []
    batch_fc_promoted = 0
    batch_fc_dropped = 0

    for idx, src in enumerate(sources, start=1):
        tracker.start(
            f"S4-{idx}-PREP",
            f"소스 {idx}/{len(sources)} 준비",
            f"{src.kind}: {src.label[:50]}",
        )
        tracker.ok(f"S4-{idx}-PREP", f"{len(src.text)}자")

        try:
            state = run_pipeline_with_steps(
                tracker,
                idx,
                src.text,
                persist_db=use_db,
                enable_dreamer=True,
                fact_checker_mode=fc_mode,
                fact_checker_dry_run=(fc_mode == "stub"),
                analysis_run_id=batch_run_id,
                source_document_meta=src.document_meta_dict(),
                corpus_fact_pool=list(corpus_pool_accum),
            )
        except Exception as exc:
            raise RuntimeError(f"파이프라인 실패 ({src.label}): {exc}") from exc

        pipeline_states.append(state)
        promoted = state.get("promoted_facts") or []
        dropped = state.get("dropped_hypotheses") or []
        batch_fc_promoted += len(promoted)
        batch_fc_dropped += len(dropped)
        corpus_pool_accum.extend(state.get("completed_facts") or [])

        tracker.start(f"S4-{idx}-REPORT", "리포트 요약")
        report = format_dry_run_report(state)
        tracker.ok(f"S4-{idx}-REPORT")

        verified = state.get("verified_edges") or []
        completed = state.get("completed_facts") or []

        if not use_db:
            tracker.start(f"S4-{idx}-SESSION-GRAPH", "세션 그래프 변환")
            session_graphs.append(graph_from_pipeline_state(state))
            tracker.ok(f"S4-{idx}-SESSION-GRAPH")

        runs.append(
            {
                "index": idx,
                "kind": src.kind,
                "label": src.label,
                "chars": len(src.text),
                "verified_edges": len(verified),
                "atomic_facts": len(completed),
                "dreamer_promoted": len(promoted),
                "dreamer_dropped": len(dropped),
                "preview": src.text[:240] + ("…" if len(src.text) > 240 else ""),
                "report_excerpt": "\n".join(report.splitlines()[:12]),
            }
        )

    if not use_db:
        use_db, neo4j_sync = _ensure_neo4j_tracked(tracker, pipeline_states)

    tracker.start("S6-GRAPH-LOAD", "그래프 데이터 로드")
    if use_db:
        tracker.ok("S6-GRAPH-LOAD", "Neo4j Cypher")
        tracker.start("S6-GRAPH-QUERY", "인과 그래프 조회", "현재 배치만")
        fetched = fetch_causal_graph(
            max_nodes=300,
            analysis_run_id=batch_run_id,
            trigger_events=batch_trigger_events,
        )
        tracker.ok(
            "S6-GRAPH-QUERY",
            f"nodes={len(fetched.nodes)} matched={fetched.matched_nodes_in_db}",
        )
    else:
        tracker.ok("S6-GRAPH-LOAD", "세션 병합")
        tracker.start("S6-GRAPH-MERGE", "세션 그래프 병합")
        fetched = merge_graph_results(session_graphs)
        tracker.ok("S6-GRAPH-MERGE", f"nodes={len(fetched.nodes)}")

    bridge_edges: list = []
    orchestration: dict | None = None
    if len(sources) >= 2 and pipeline_states:
        from deconstructor.web.corpus_bridge import attach_bridge_edges, build_orchestration_meta

        fetched, bridge_edges = attach_bridge_edges(fetched, pipeline_states)
        orchestration = build_orchestration_meta(pipeline_states, len(bridge_edges))
        if bridge_edges:
            tracker.start("S6-GRAPH-BRIDGE", "교차 문서 bridge", f"{len(bridge_edges)}건")
            tracker.ok("S6-GRAPH-BRIDGE")

    if orchestration is not None:
        from deconstructor.corpus.ingest_hook import cross_run_corpus_enabled

        if cross_run_corpus_enabled():
            orchestration = {**orchestration, "corpus_scope": "cross_run"}

    _render_graph_tracked(tracker, fetched.nodes, fetched.edges)

    from deconstructor.guards import build_watch_report
    from deconstructor.recompose import recompose_index
    from deconstructor.skeleton import skeleton_index
    from deconstructor.web.debug_report import build_pipeline_debug

    skeleton = skeleton_index(list(fetched.nodes), list(fetched.edges))
    from deconstructor.spine.api_payload import build_link_rationales_payload, build_spine_payload

    spine = build_spine_payload(list(fetched.nodes), list(fetched.edges))
    link_rationales = build_link_rationales_payload(list(fetched.nodes), list(fetched.edges))
    fc_block = {
        "mode": fc_mode,
        "corpus_pool_size": len(corpus_pool_accum),
        "batch_promoted": batch_fc_promoted,
        "batch_dropped": batch_fc_dropped,
        "tavily_disabled": not has_tavily,
    }
    recompose = recompose_index(
        list(fetched.nodes),
        list(fetched.edges),
        skeleton,
        fact_checker=fc_block,
        items_processed=len(sources),
    )

    pipeline_debug = build_pipeline_debug(
        pipeline_states,
        fetched=fetched,
        batch_run_id=batch_run_id,
        fact_checker_mode=fc_mode,
    )

    watch = build_watch_report(
        pipeline_states=pipeline_states,
        skeleton=skeleton,
        node_count=len(fetched.nodes),
    )

    result = {
        "ok": True,
        "steps": tracker.to_list(),
        "neo4j": use_db,
        "neo4j_sync": neo4j_sync,
        "neo4j_persisted": use_db,
        "items_processed": len(sources),
        "sources": runs,
        "nodes": len(fetched.nodes),
        "edges": len(fetched.edges),
        "graph_filter": {
            "analysis_run_id": batch_run_id,
            "trigger_events": batch_trigger_events,
            "matched_nodes_in_db": fetched.matched_nodes_in_db,
            "total_nodes_in_db": fetched.total_nodes_in_db,
        },
        "verified_edges_total": sum(r["verified_edges"] for r in runs),
        "atomic_facts_total": sum(r["atomic_facts"] for r in runs),
        "orchestration": orchestration,
        "pipeline_debug": pipeline_debug,
        "skeleton": skeleton,
        "spine": spine,
        "link_rationales": link_rationales,
        "recompose": recompose,
        "fact_checker": fc_block,
        "watch": watch,
        "read_verify": read_verify_payload,
    }

    from deconstructor.corpus.ingest_hook import maybe_append_batch_corpus

    maybe_append_batch_corpus(
        result,
        pipeline_states,
        run_id=batch_run_id,
        session_id=os.getenv("LINK_SESSION_ID") or batch_run_id,
    )

    return result
