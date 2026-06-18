"""
workflow — graph.builder 하위 호환 re-export
============================================

## 목적 / Purpose

`from deconstructor.graph.workflow import build_graph, run_pipeline` 구 import를
유지한다. 구현은 전부 `builder.py`에 있다.

Preserves legacy imports
`from deconstructor.graph.workflow import build_graph, run_pipeline`.
All implementation is in `builder.py`.

## 파이프라인 위치 / Pipeline Position

레거시 테스트·외부 스크립트용. 신규 코드는 `deconstructor.graph` 또는
`deconstructor.graph.builder` 사용.

For legacy tests/scripts. New code should use `deconstructor.graph` or
`deconstructor.graph.builder`.

## 수정 가이드 / Modification Guide

- 이 파일에 로직 추가 금지 — `builder.py`만 수정.
"""

from deconstructor.graph.builder import build_graph, run_pipeline

__all__ = ["build_graph", "run_pipeline"]
