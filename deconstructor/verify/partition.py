"""
partition — verify 단계 순수 분할 로직
======================================

## 목적 / Purpose

`AtomicFact.is_atomic` 플래그만으로 facts 리스트를 두 부분집합으로 나눈다.
LangGraph·I/O 의존성 없이 **단위 테스트 가능한 순수 함수**이다.

Splits a fact list into two subsets using only `AtomicFact.is_atomic`.
A **pure, unit-testable** function with no LangGraph or I/O dependencies.

## 파이프라인 위치 / Pipeline Position

::

    verify_node → partition_by_atomicity → (atomic, non_atomic)

deconstruct LLM/스텁이 설정한 `is_atomic` 값을 신뢰한다. 별도 LLM 호출 없음.

Trusts `is_atomic` set by deconstruct LLM/stub. No additional LLM calls.

## 수정 가이드 / Modification Guide

- Micro-step V-1/V-2 주석은 요구사항 추적용 — 로직 변경 시 주석 갱신.
- 복합 조건(예: subject 비어 있음 → non-atomic 강제) 추가 시 skeptic 입력 품질 영향 검토.
- 반환 튜플 순서 `(atomic, non_atomic)` — `verify_node`와 모든 호출부 일치 유지.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact


def partition_by_atomicity(
    facts: list[AtomicFact],
) -> tuple[list[AtomicFact], list[AtomicFact]]:
    """
    Split facts into (atomic, non_atomic).

    Micro-step V-1: filter is_atomic=True.
    Micro-step V-2: filter is_atomic=False.

    facts를 (원자 목록, 비원자 목록) 튜플로 반환한다.
    """
    # V-1: 더 이상 쪼갤 수 없다고 표시된 crumb
    atomic = [f for f in facts if f.is_atomic]
    # V-2: deconstruct 루프로 돌아갈 crumb
    non_atomic = [f for f in facts if not f.is_atomic]
    return atomic, non_atomic
