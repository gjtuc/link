"""
after_verify — verify 직후 조건부 라우팅
========================================

## 목적 / Purpose

비원자 crumb이 남아 있고 recursion depth가 상한 미만이면 **deconstruct**로 루프,
그렇지 않으면 **skeptic**으로 탈출한다. depth 상한 도달 시 partial_run 경로로 skeptic 진행.

If non-atomic crumbs remain and recursion depth is below the cap, loop to **deconstruct**;
otherwise exit to **skeptic**. At depth cap, proceed to skeptic (partial_run path).

## 파이프라인 위치 / Pipeline Position

::

    verify_node → route_after_verify(state) → "deconstruct" | "skeptic"
         ↑___________________|
              (loop)

LangGraph `conditional_edges`의 **유일한 라우팅 함수**(현재 그래프 기준).

The **sole routing function** for LangGraph `conditional_edges` in the current graph.

## 수정 가이드 / Modification Guide

- Micro-step R-1/R-2/R-3: 요구사항 추적 — 로직 변경 시 주석·테스트 동기화.
- `MAX_RECURSION_DEPTH`(`graph/builder.py`)와 `make_initial_state` 기본 cap 일치 유지.
- 새 종료 조건(예: 빈 completed_facts) 추가 시 skeptic/weaver 빈 입력 동작 확인.
- 반환 문자열은 `add_conditional_edges` 맵 키와 **정확히** 일치해야 함.
"""

from __future__ import annotations

from typing import Literal

from deconstructor.pipeline.state import State


def route_after_verify(state: State) -> Literal["deconstruct", "skeptic"]:
    """
    Micro-step R-1: null floor -> skeptic.
    Micro-step R-2: non-atomic + under cap -> deconstruct.
    Micro-step R-3: non-atomic + at cap -> skeptic (partial_run path).

  R-1: 분해 대기열 비음 → skeptic.
  R-2: 비원자 남음 + depth < cap → deconstruct 재진입.
  R-3: 비원자 남음 + depth >= cap → skeptic (부분 실행).
    """
    # R-1: extracted_facts 비었으면 분해 완료(또는 초기 실패) — skeptic로
    if not state["extracted_facts"]:
        return "skeptic"

    # R-3: depth 상한 도달 — 더 쪼개지 않고 skeptic에서 인과 검증만
    if state["recursion_depth"] >= state["max_recursion_depth"]:
        return "skeptic"

    # R-2: 아직 쪼갤 비원자 crumb 있음 — deconstruct 루프
    return "deconstruct"
