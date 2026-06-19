"""
verify_node — LangGraph 원자성 검증 노드
========================================

## 목적 / Purpose

`extracted_facts`를 원자/비원자로 분할해 State를 갱신한다. 원자 사실은 skeptic 단계로
넘어갈 `completed_facts` 풀에 누적되고, 비원자는 deconstruct 루프로 되돌아간다.

Partitions `extracted_facts` into atomic vs non-atomic and updates State. Atomic facts
accumulate in `completed_facts` for skeptic; non-atomic return to the deconstruct loop.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct → verify_node → route_after_verify
                      ↓
         extracted_facts (non-atomic only)
         completed_facts   (+ atomic batch)

deconstruct 직후 **항상** 실행되는 고정 엣지 노드이다.

Always runs on the fixed edge immediately after deconstruct.

## 수정 가이드 / Modification Guide

- 분할 로직 → `partition.partition_by_atomicity` (단위 테스트 용이).
- `completed_facts` 누적 vs 교체: 현재는 **교체가 아닌 배치 이동** — skeptic가 전체 목록 사용.
- 노드 반환은 `extracted_facts`, `completed_facts` 키만 — 다른 필드는 라우터·skeptic가 처리.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State
from deconstructor.provenance.assign import tag_as_extracted
from deconstructor.verify.partition import partition_by_atomicity


def verify_node(state: State) -> dict:
    """
    Move atomic crumbs to completed_facts; keep non-atomic in extracted_facts.

    [PROV-S1-3] atomic 이동 시 source_type=extracted 강제.
    """
    atomic, non_atomic = partition_by_atomicity(state["extracted_facts"])
    tagged_atomic = tag_as_extracted(atomic)
    return {
        "extracted_facts": non_atomic,
        "completed_facts": tagged_atomic,
    }
