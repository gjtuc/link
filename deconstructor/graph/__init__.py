"""
graph 패키지 — LangGraph 워크플로우 컴파일·실행
===============================================

## 목적 / Purpose

deconstructor 파이프라인 전체를 **LangGraph StateGraph**로 조립·컴파일하고,
`run_pipeline`으로 1회 invoke하는 canonical API를 제공한다.

Assembles the full deconstructor pipeline as a **LangGraph StateGraph**, compiles it,
and exposes `run_pipeline` for a single invoke — the canonical API.

## 파이프라인 위치 / Pipeline Position

::

    cli/modes/live.py → graph.run_pipeline
    tests             → graph.build_graph

전체 토폴로지: deconstruct → verify ⇄ deconstruct | skeptic → weaver → END

Full topology: deconstruct → verify ⇄ deconstruct | skeptic → weaver → END

## 수정 가이드 / Modification Guide

- 그래프 로직은 `builder.py` — `workflow.py`는 re-export shim.
- 노드 추가·엣지 변경 → `builder.build_graph` + `pipeline/state.py` 필드.
- `graph_builder.py`(루트)도 동일 심볼 re-export — 중복 문서화 최소화.
"""

from deconstructor.graph.builder import build_graph, run_pipeline

__all__ = ["build_graph", "run_pipeline"]
