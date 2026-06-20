"""
LangGraph 컴파일 및 파이프라인 실행 진입점 (Canonical Graph Builder)
=====================================================================

STAGE 0-1 (제품 계약) — 코어 DAG (변경 금지 방향)
-------------------------------------------------
  완성품 → **Deconstruct(해체)** → Verify(粒度) → Dreamer(빈 因) →
  Fact-Checker(상함 검사) → Skeptic(因→과 법칙) → Weaver → END

  - ζ-2 부스러기: Deconstruct + Verify
  - ζ-3 상함/태움: Fact-Checker drop + Skeptic reject
  - ζ-4 괜찮은 부위: extracted + verified edges
  - ζ-5 빈 연결: Dreamer → Fact-Checker
  - 0-1에서 **고치지 않는** 레이어; Ingest(1)·Presentation(9)·Orchestration(2) 가 계약.

STAGE 0-5 (Roadmap) — skeleton index (future)
-----------------------------------------------
  - Sprint 3 ✅: prompts + compound heuristic — ``SPRINT-3-deconstruct-depth-spec.md``
  - Sprint 4: SP4-IDX-* — G-SKP-INDEX (AC-SKP-03,04)
  - D-06: 코어 DAG 토폴로지 불변
  - See ``docs/design/STAGE-0-5-implementation-roadmap.md`` Appendix E

Step 4 토폴로지 (--enable-dreamer):

    deconstruct → verify ⇄ loop
                    ↓
              dreamer (Flash 15~20 → Pro ≤5) → fact_checker → skeptic → weaver → END

기본 (enable_dreamer=False):

    deconstruct → verify ⇄ loop → skeptic → weaver → END
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from deconstructor import config
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
    dreamer_dry_run: bool | None = None,
    fact_checker_dry_run: bool | None = None,
    fact_checker_mode: str | None = None,
    persist_db: bool = False,
    enable_dreamer: bool = False,
):
    """
    LangGraph StateGraph 컴파일.

    Args:
        dry_run: stub deconstruct / skeptic mechanism (dreamer·fact_checker는 별도 인자).
        dreamer_dry_run: None이면 dry_run과 동일.
        fact_checker_dry_run: Legacy bool; True→stub. Prefer ``fact_checker_mode``.
        fact_checker_mode: ``live`` | ``corpus`` | ``stub`` (Sprint 5).
        persist_db: Neo4j weaver + ghost persist.
        enable_dreamer: verify 탈출 시 dreamer→fact_checker 경로.
    """
    _dreamer_dry = dry_run if dreamer_dry_run is None else dreamer_dry_run
    if fact_checker_mode is None:
        if fact_checker_dry_run is True:
            _fc_mode = "stub"
        elif fact_checker_dry_run is False:
            _fc_mode = "live" if config.tavily_enabled() else config.resolve_fact_checker_mode()
        else:
            _fc_mode = config.resolve_fact_checker_mode()
    else:
        _fc_mode = fact_checker_mode

    workflow = StateGraph(State)

    deconstruct = deconstruct_node_stub if dry_run else deconstruct_node
    workflow.add_node("deconstruct", deconstruct)
    workflow.add_node("verify", verify_node)
    workflow.add_node("skeptic", partial(skeptic_node, dry_run=dry_run))
    workflow.add_node("weaver", partial(weaver_node, persist_db=persist_db))

    if enable_dreamer:
        print(
            "[STEP4-build] wiring dreamer → fact_checker → skeptic "
            f"(dreamer_dry={_dreamer_dry}, fact_checker_mode={_fc_mode})"
        )
        workflow.add_node("dreamer", partial(dreamer_node, dry_run=_dreamer_dry))
        workflow.add_node(
            "fact_checker", partial(fact_checker_node, mode=_fc_mode)
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
    dreamer_dry_run: bool | None = None,
    fact_checker_dry_run: bool | None = None,
    persist_db: bool = False,
    enable_dreamer: bool = False,
) -> State:
    """헤드라인으로 전체 파이프라인 1회 실행."""
    graph = build_graph(
        dry_run=dry_run,
        dreamer_dry_run=dreamer_dry_run,
        fact_checker_dry_run=fact_checker_dry_run,
        persist_db=persist_db,
        enable_dreamer=enable_dreamer,
    )
    initial = make_initial_state(
        raw_text,
        max_recursion_depth=max_recursion_depth,
        enable_dreamer=enable_dreamer,
    )
    return graph.invoke(initial)
