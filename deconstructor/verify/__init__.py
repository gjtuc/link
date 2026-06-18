"""
verify 패키지 — 원자성(atomicity) 검증 및 facts 분할
====================================================

## 목적 / Purpose

deconstruct가 생성한 `extracted_facts`를 **원자(atomic)** 와 **비원자(non-atomic)** 로
나누어, 원자 crumb은 `completed_facts`로, 비원자는 재분해 대기열에 남긴다.

Partitions `extracted_facts` from deconstruct into **atomic** and **non-atomic**
crumbs: atomic → `completed_facts`, non-atomic → remain for re-decomposition.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct → verify (this package) → route_after_verify

LangGraph 노드 `verify_node`와 순수 함수 `partition_by_atomicity`를 export한다.

Exports LangGraph node `verify_node` and pure function `partition_by_atomicity`.

## 수정 가이드 / Modification Guide

- 분할 기준 변경 → `partition.py` (현재 `is_atomic` 플래그만 사용).
- 새 검증 단계(예: 타임스탬프 정합성) → `node.py`에서 partition 후 추가 로직; State 필드 검토.
- 라우팅 정책은 `routing/after_verify.py` — verify는 분할만 담당.
"""

from deconstructor.verify.node import verify_node
from deconstructor.verify.partition import partition_by_atomicity

__all__ = ["partition_by_atomicity", "verify_node"]
