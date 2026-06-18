"""
deconstruct 패키지 — 기계적 텍스트 분해 (Mechanical Text Decomposition)
=========================================================================

## 목적 / Purpose

뉴스 헤드라인·이벤트 문장을 **원자적 사실(AtomicFact)** 목록으로 분해하는 LangGraph 노드와
그 지원 모듈을 제공한다. LLM 경로(`deconstruct_node`)와 결정론적 스텁 경로
(`deconstruct_node_stub`)를 모두 노출한다.

Provides LangGraph nodes and helpers that split headlines/events into **AtomicFact**
lists. Exposes both the LLM path (`deconstruct_node`) and the deterministic stub
path (`deconstruct_node_stub`).

## 파이프라인 위치 / Pipeline Position

::

    [deconstruct] → verify → (loop back to deconstruct | skeptic → weaver)

이 패키지는 그래프 **진입점(entry)** 및 verify 이후 **재진입 루프**에서 실행된다.
`extracted_facts`를 채우거나, 비원자 crumb 하나를 더 세분화된 자식 facts로 교체한다.

This package runs at the graph **entry point** and on **re-entry** after verify.
It fills `extracted_facts` or replaces one non-atomic crumb with finer child facts.

## 수정 가이드 / Modification Guide

- **새 분해 전략**: `input.py`에 target resolver 추가, `node.py` 또는 `stub_node.py`에서 호출.
- **프롬프트 변경**: `prompts.py`만 수정 — LLM 출력 스키마(`FactList`)와 일치해야 함.
- **상태 병합 규칙**: `apply.py` → `state_merge.merge_refined_facts`; 테스트는 `tests/` 격리.
- **그래프 등록**: `graph/builder.py`의 `add_node("deconstruct", ...)` 바인딩 확인.
- dry_run 플래그는 stub 노드로 스위칭; live 경로는 API 키(`llm/`) 필요.

Exports the two public node callables for graph wiring and backward-compatible imports.
"""

from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.deconstruct.stub_node import deconstruct_node_stub

__all__ = ["deconstruct_node", "deconstruct_node_stub"]
