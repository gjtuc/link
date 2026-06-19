"""LangGraph node wrapper for The Weaver (Step 4 ghost persist)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deconstructor.agents.watcher.run import run_watcher_in_memory, run_watcher_neo4j
from deconstructor.weaver.console_store import ConsoleWeaver
from deconstructor.weaver.neo4j_store import Neo4jWeaver
from deconstructor.weaver.resolve import (
    facts_for_verified_edges,
    orphan_atomic_completed_facts,
)

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State


def weaver_node(state: "State", *, persist_db: bool) -> dict:
    """
    Persist verified edges + endpoint facts; ghost dropped hypotheses separately.
    """
    edges = state["verified_edges"]
    all_facts = list(state["completed_facts"]) + list(
        state.get("promoted_facts") or []
    )
    facts = facts_for_verified_edges(all_facts, edges)
    endpoint_ids = {f.id for f in facts}
    ghost_facts = [
        d.ghost_fact for d in (state.get("dropped_hypotheses") or [])
    ]
    orphan_promoted = [
        f
        for f in (state.get("promoted_facts") or [])
        if f.id not in endpoint_ids
    ]
    orphan_extracted = orphan_atomic_completed_facts(
        state.get("completed_facts") or [],
        already_persisted_ids=endpoint_ids
        | {f.id for f in orphan_promoted}
        | {f.id for f in ghost_facts},
    )
    partial_run = state.get("partial_run", False)

    if persist_db:
        store = Neo4jWeaver()
        try:
            result = store.persist(
                trigger_event=state["raw_text"],
                analysis_run_id=state["analysis_run_id"],
                facts=facts,
                edges=edges,
                partial_run=partial_run,
            )
            ghosts_written = 0
            extra_facts = (
                list(ghost_facts) + list(orphan_promoted) + list(orphan_extracted)
            )
            if extra_facts:
                print(
                    f"[STEP4-weaver] persist_ghost_facts count={len(extra_facts)} "
                    f"(ghosts={len(ghost_facts)}, promoted_orphans={len(orphan_promoted)}, "
                    f"extracted_orphans={len(orphan_extracted)})"
                )
                ghosts_written = store.persist_ghost_facts(
                    trigger_event=state["raw_text"],
                    analysis_run_id=state["analysis_run_id"],
                    facts=extra_facts,
                )
            if ghosts_written:
                result = result.model_copy(
                    update={"ghosts_written": ghosts_written}
                )
            critical_subjects = run_watcher_neo4j(store._driver)
            if critical_subjects:
                result = result.model_copy(
                    update={"critical_subjects": critical_subjects}
                )
        finally:
            store.close()
    else:
        result = ConsoleWeaver().persist(
            trigger_event=state["raw_text"],
            facts=facts,
            edges=edges,
            partial_run=partial_run,
        )
        if ghost_facts or orphan_promoted:
            print(
                f"[STEP4-weaver] console mode: {len(ghost_facts)} ghost(s), "
                f"{len(orphan_promoted)} promoted orphan(s) (not persisted without --db)"
            )
        critical_subjects = run_watcher_in_memory(facts, edges)
        if critical_subjects:
            result = result.model_copy(
                update={"critical_subjects": critical_subjects}
            )

    return {"weaver_result": result}
