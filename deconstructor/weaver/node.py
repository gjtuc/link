"""LangGraph node wrapper for The Weaver (Step 4 ghost persist)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deconstructor.agents.watcher.run import run_watcher_in_memory, run_watcher_neo4j
from deconstructor.weaver.console_store import ConsoleWeaver
from deconstructor.weaver.neo4j_store import Neo4jWeaver
from deconstructor.weaver.resolve import facts_for_verified_edges

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
    ghost_facts = [
        d.ghost_fact for d in (state.get("dropped_hypotheses") or [])
    ]
    partial_run = state.get("partial_run", False)

    if persist_db:
        store = Neo4jWeaver()
        try:
            result = store.persist(
                trigger_event=state["raw_text"],
                facts=facts,
                edges=edges,
                partial_run=partial_run,
            )
            ghosts_written = 0
            if ghost_facts:
                print(
                    f"[STEP4-weaver] persist_ghost_facts count={len(ghost_facts)}"
                )
                ghosts_written = store.persist_ghost_facts(
                    trigger_event=state["raw_text"],
                    facts=ghost_facts,
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
        if ghost_facts:
            print(
                f"[STEP4-weaver] console mode: {len(ghost_facts)} ghost(s) "
                f"(not persisted without --db)"
            )
        critical_subjects = run_watcher_in_memory(facts, edges)
        if critical_subjects:
            result = result.model_copy(
                update={"critical_subjects": critical_subjects}
            )

    return {"weaver_result": result}
