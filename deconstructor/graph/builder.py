"""
LangGraph 컴파일 및 파이프라인 실행 진입점 (Canonical Graph Builder)
=====================================================================

Step 4 토폴로지 (--enable-dreamer):

    deconstruct → verify ⇄ loop
                    ↓
              dreamer → fact_checker → skeptic → weaver → END

기본 (enable_dreamer=False):

    deconstruct → verify ⇄ loop → skeptic → weaver → END
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.fact_checker.node import fact_checker_node
from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.pipeline.state import State
from deconstructor.pipeline.state_factory import make_initial_state
from deconstructor.routing.after_verify import route_after_verify
from deconstructor.skeptic.node import skeptic_node
from deconstructor.verify.node import verify_node
from deconstructor.weaver.node import weaver_node

MAX_RECURSION_DEPTH = 5


def build_graph(
    *,
    dry_run: bool = False,
    persist_db: bool = False,
    enable_dreamer: bool = False,
):
    """
    LangGraph StateGraph 컴파일.

    Args:
        dry_run: stub deconstruct / dreamer / fact_checker / skeptic mechanism.
        persist_db: Neo4j weaver + ghost persist.
        enable_dreamer: verify 탈출 시 dreamer→fact_checker 경로.
    """
    workflow = StateGraph(State)

    deconstruct = deconstruct_node_stub if dry_run else deconstruct_node
    workflow.add_node("deconstruct", deconstruct)
    workflow.add_node("verify", verify_node)
    workflow.add_node("skeptic", partial(skeptic_node, dry_run=dry_run))
    workflow.add_node("weaver", partial(weaver_node, persist_db=persist_db))

    if enable_dreamer:
        print("[STEP4-build] wiring dreamer → fact_checker → skeptic")
        workflow.add_node("dreamer", partial(dreamer_node, dry_run=dry_run))
        workflow.add_node(
            "fact_checker", partial(fact_checker_node, dry_run=dry_run)
        )
        route_map = {
            "deconstruct": "deconstruct",
            "dreamer": "dreamer",
            "skeptic": "skeptic",
        }
    else:
        route_map = {
            "deconstruct": "deconstruct",
            "skeptic": "skeptic",
        }

    workflow.set_entry_point("deconstruct")
    workflow.add_edge("deconstruct", "verify")
    workflow.add_conditional_edges("verify", route_after_verify, route_map)

    if enable_dreamer:
        workflow.add_edge("dreamer", "fact_checker")
        workflow.add_edge("fact_checker", "skeptic")

    workflow.add_edge("skeptic", "weaver")
    workflow.add_edge("weaver", END)

    return workflow.compile()


def run_pipeline(
    raw_text: str,
    *,
    max_recursion_depth: int | None = None,
    dry_run: bool = False,
    persist_db: bool = False,
    enable_dreamer: bool = False,
) -> State:
    """헤드라인으로 전체 파이프라인 1회 실행."""
    graph = build_graph(
        dry_run=dry_run,
        persist_db=persist_db,
        enable_dreamer=enable_dreamer,
    )
    initial = make_initial_state(
        raw_text,
        max_recursion_depth=max_recursion_depth,
        enable_dreamer=enable_dreamer,
    )
    return graph.invoke(initial)
