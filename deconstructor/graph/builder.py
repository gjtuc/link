"""
LangGraph 컴파일 및 파이프라인 실행 진입점 (Canonical Graph Builder)
=====================================================================

## 목적 / Purpose

deconstruct → verify → (conditional loop) → skeptic → weaver **전체 워크플로우**를
`StateGraph`로 정의·컴파일하고, 초기 State를 만들어 `invoke`한다.
`dry_run`·`persist_db` 플래그로 stub/Neo4j 등을 런타임에 바인딩한다.

Defines, compiles, and invokes the full deconstruct → verify → (conditional loop) →
skeptic → weaver workflow as a `StateGraph`. Binds stub/Neo4j etc. at runtime via
`dry_run` and `persist_db` flags.

## 파이프라인 위치 / Pipeline Position

## 그래프 토폴로지 / Graph Topology

::

    [deconstruct] → [verify] ──(conditional)──→ [deconstruct]  (loop)
                              └──→ [skeptic] → [weaver] → END

## 노드 바인딩 / Node Binding

- ``dry_run=True``  → ``deconstruct_node_stub`` (deterministic FactList)
- ``dry_run=False`` → ``deconstruct_node`` (LLM)
- ``persist_db=True`` → ``weaver_node(persist_db=True)`` → Neo4jWeaver
- ``persist_db=False`` → ConsoleWeaver (default)

CLI live·library 호출의 **중심 진입점**. `pipeline_trace`는 별도 trace 래퍼 사용.

Central entry for CLI live and library calls. `pipeline_trace` uses a separate trace wrapper.

## 수정 가이드 / Modification Guide

- 새 LangGraph 노드: ``add_node`` + ``add_edge``/``conditional_edges``, ``State`` 필드 추가(``pipeline/state.py``).
- ``MAX_RECURSION_DEPTH``: ``state_factory`` 와 ``routing/after_verify`` 와 일관성 유지.
- conditional 라우터 반환값은 ``add_conditional_edges`` 맵 키와 정확히 일치.
- 테스트: ``tests/smoke/`` 및 ``test_run.py``.
- 루트 ``graph_builder.py`` shim — public API 변경 시 re-export 동기화.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.pipeline.state import State
from deconstructor.pipeline.state_factory import make_initial_state
from deconstructor.routing.after_verify import route_after_verify
from deconstructor.skeptic.node import skeptic_node
from deconstructor.verify.node import verify_node
from deconstructor.weaver.node import weaver_node

# state_factory 기본값과 동일 — CLI --depth-cap 시 별도 cap 전달 가능
MAX_RECURSION_DEPTH = 5


def build_graph(*, dry_run: bool = False, persist_db: bool = False):
    """
    LangGraph StateGraph 컴파일.

    Args:
        dry_run: True면 LLM 대신 stub deconstruct + skeptic mechanism stub.
        persist_db: True면 weaver가 Neo4j에 MERGE (--db 플래그).

    Returns:
        컴파일된 Runnable (invoke/stream 가능).
    """
    workflow = StateGraph(State)

    # dry_run 에 따라 deconstruct 구현체 교체 (나머지 노드는 동일 시그니처)
    deconstruct = deconstruct_node_stub if dry_run else deconstruct_node
    workflow.add_node("deconstruct", deconstruct)
    workflow.add_node("verify", verify_node)
    # skeptic도 dry_run 시 mechanism stub 사용 (partial로 플래그 주입)
    workflow.add_node("skeptic", partial(skeptic_node, dry_run=dry_run))
    workflow.add_node("weaver", partial(weaver_node, persist_db=persist_db))

    workflow.set_entry_point("deconstruct")
    # deconstruct 후 항상 verify — atomicity 분할
    workflow.add_edge("deconstruct", "verify")
    # verify 후: non-atomic 남음 + depth 미만 → deconstruct, 아니면 skeptic
    workflow.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "deconstruct": "deconstruct",
            "skeptic": "skeptic",
        },
    )
    # skeptic → weaver → 종료 (루프 없음)
    workflow.add_edge("skeptic", "weaver")
    workflow.add_edge("weaver", END)

    return workflow.compile()


def run_pipeline(
    raw_text: str,
    *,
    max_recursion_depth: int | None = None,
    dry_run: bool = False,
    persist_db: bool = False,
) -> State:
    """
    헤드라인(또는 임의 텍스트)으로 전체 파이프라인 1회 실행.

    Args:
        raw_text: 입력 뉴스/헤드라인. State.raw_text 및 Neo4j trigger_event 로 보존.
        max_recursion_depth: deconstruct 루프 상한. None이면 config/state_factory 기본값.
        dry_run: stub 모드 (LLM 비용 없음).
        persist_db: Neo4j 영속화.

    Returns:
        최종 LangGraph State (completed_facts, verified_edges, weaver_result 등).
    """
    graph = build_graph(dry_run=dry_run, persist_db=persist_db)
    # 초기 State: raw_text, depth 카운터, 빈 fact/edge 리스트
    initial = make_initial_state(raw_text, max_recursion_depth=max_recursion_depth)
    return graph.invoke(initial)
