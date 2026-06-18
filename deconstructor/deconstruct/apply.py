"""
apply — deconstruct 결과를 파이프라인 State에 반영
==================================================

## 목적 / Purpose

LLM 또는 스텁이 반환한 `FactList`를 `extracted_facts`에 병합하고 `recursion_depth`를
1 증가시킨다. 노드(`node.py`, `stub_node.py`)와 순수 병합 로직(`state_merge.py`) 사이의
**얇은 조정 계층**.

Merges a `FactList` into `extracted_facts` and increments `recursion_depth` by one.
Thin orchestration layer between nodes (`node.py`, `stub_node.py`) and pure merge
logic (`state_merge.py`).

## 파이프라인 위치 / Pipeline Position

::

    deconstruct_node(_stub) → apply_deconstruct_result → State delta

반환 dict는 LangGraph가 기존 State에 **부분 병합(partial update)** 한다.
`verify_node`는 이후 `extracted_facts`를 atomic/non-atomic으로 분할한다.

Returned dict is **partial-updated** into State by LangGraph.
`verify_node` then partitions `extracted_facts` by atomicity.

## 수정 가이드 / Modification Guide

- 부모 crumb 교체 규칙 → `state_merge.merge_refined_facts` (테스트 격리).
- depth 정책 변경 시 `routing/after_verify.py`의 `max_recursion_depth` 비교와 일치시킬 것.
- 초기 분해(`parent_id is None`)는 `result.facts`로 전체 교체 — 기존 pending 무시.
- 새 State 필드 추가 시 모든 노드 반환 dict와 `pipeline/state.py` TypedDict 동기화.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact, FactList
from deconstructor.state_merge import merge_refined_facts


def apply_deconstruct_result(
    *,
    pending: list[AtomicFact],
    parent_id: str | None,
    result: FactList,
    recursion_depth: int,
) -> dict:
    """
    Merge FactList into extracted_facts and bump recursion_depth.

    FactList를 extracted_facts에 병합하고 recursion_depth를 1 증가시킨 partial state 반환.
    """
    if parent_id is not None:
        # 재분해: parent_id crumb 제거 후 자식 facts append
        updated = merge_refined_facts(pending, parent_id, result.facts)
    else:
        # 첫 분해: LLM/스텁 결과가 extracted_facts 전체를 대체
        updated = result.facts

    return {
        "extracted_facts": updated,
        "recursion_depth": recursion_depth + 1,
    }
