"""
routing 패키지 — LangGraph 조건부 엣지(conditional edges)
==========================================================

## 목적 / Purpose

verify 이후 파이프라인이 **deconstruct 루프**로 돌아갈지 **skeptic**으로 진행할지
결정하는 라우팅 함수를 제공한다.

Provides routing functions that decide whether the pipeline **loops to deconstruct**
or **proceeds to skeptic** after verify.

## 파이프라인 위치 / Pipeline Position

::

    verify → route_after_verify → "deconstruct" | "skeptic"

`graph/builder.py`의 `add_conditional_edges("verify", route_after_verify, {...})`에 연결.

Wired in `graph/builder.py` via
`add_conditional_edges("verify", route_after_verify, {...})`.

## 수정 가이드 / Modification Guide

- 새 분기 추가 시 `Literal` 반환 타입·conditional_edges 맵 키·대상 노드 이름 동시 수정.
- depth 상한은 `State.max_recursion_depth`와 `recursion_depth` 비교 — `state_factory` 기본값 확인.
- partial_run 플래그는 skeptic/weaver에서 설정; 라우터는 extracted_facts·depth만 본다.
"""

from deconstructor.routing.after_verify import route_after_verify

__all__ = ["route_after_verify"]
