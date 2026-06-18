"""Phase 10 — Weaver console (--no-db default)."""

from __future__ import annotations

from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.weaver.resolve import facts_for_verified_edges
from tests.smoke.harness import StepRunner


def phase_10_weaver_dry(run: StepRunner, headline: str) -> None:
    run.section("10a traced pipeline weaver step")

    traced = run_pipeline_traced(headline, dry_run=True, persist_db=False)
    st = traced.final_state
    run.check("weaver in sequence", traced.node_sequence[-1] == "weaver")
    run.check("weaver_result set", st["weaver_result"] is not None)
    run.check("console mode", st["weaver_result"].mode == "console")

    run.section("10b only verified edge endpoints")

    edges = st["verified_edges"]
    resolved = facts_for_verified_edges(st["completed_facts"], edges)
    if edges:
        endpoint_ids = set()
        for e in edges:
            endpoint_ids.add(e.source_fact_id)
            endpoint_ids.add(e.target_fact_id)
        run.check(
            "resolved ids match endpoints",
            {f.id for f in resolved} == endpoint_ids,
        )
        run.check(
            "weaver nodes match resolved",
            st["weaver_result"].nodes_written == len(resolved),
        )
    else:
        run.check("no edges ok", st["weaver_result"].edges_written == 0)

    run.section("10c complete run not partial")

    run.check("partial_run false", st["partial_run"] is False)
    run.check("weaver partial_run false", st["weaver_result"].partial_run is False)
