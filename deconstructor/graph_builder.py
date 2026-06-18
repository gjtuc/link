"""
graph_builder — 하위 호환 re-export 셔머 (Backward-Compatible Shim)
===================================================================

## 목적 / Purpose

구버전 import 경로(`from deconstructor.graph_builder import ...`)를 유지한다.
실제 그래프 컴파일·실행 로직은 `graph/builder.py`에 있으며, 노드·라우터는 각 패키지에서 import.

Preserves legacy import paths (`from deconstructor.graph_builder import ...`).
Actual graph compile/run logic lives in `graph/builder.py`; nodes and routers import
from their packages.

## 파이프라인 위치 / Pipeline Position

::

    cli/modes/live.py → graph_builder.run_pipeline (re-export)
    tests / external code → build_graph, deconstruct_node, verify_node, ...

신규 코드는 `deconstructor.graph.builder` 사용을 권장한다.

New code should prefer `deconstructor.graph.builder`.

## 수정 가이드 / Modification Guide

- **로직 변경 금지** — 이 파일은 re-export만; 수정은 `graph/builder.py` 및 각 노드 모듈.
- `__all__`에 새 심볼 추가 시 하위 호환 필요 여부 검토.
- deprecated 주석 유지하여 IDE/문서에서 canonical 경로 안내.
"""

from deconstructor.graph.builder import (
    MAX_RECURSION_DEPTH,
    build_graph,
    run_pipeline,
)
from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.routing.after_verify import route_after_verify
from deconstructor.verify.node import verify_node

__all__ = [
    "MAX_RECURSION_DEPTH",
    "build_graph",
    "deconstruct_node",
    "deconstruct_node_stub",
    "route_after_verify",
    "run_pipeline",
    "verify_node",
]
