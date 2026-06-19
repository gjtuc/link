"""
deconstruct_node — LLM 기반 LangGraph 분해 노드
===============================================

## 목적 / Purpose

파이프라인 State에서 분해 대상 텍스트를 해석하고, LLM을 호출해 구조화된 `FactList`를
받은 뒤 `extracted_facts`에 병합한다. **live 모드**(`dry_run=False`)의 deconstruct 구현체.

Resolves decompose target text from pipeline State, invokes the LLM for a structured
`FactList`, and merges into `extracted_facts`. This is the **live** deconstruct
implementation when `dry_run=False`.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct (this module) → verify → route_after_verify
         ↑__________________________________|
              (non-atomic crumbs remain)

첫 패스: `raw_text` 전체 분해. 재진입 패스: `pending[0]`의 `subject | state_change` 재분해.

First pass: decompose full `raw_text`. Re-entry: re-split `pending[0]` as
`subject | state_change`.

## 수정 가이드 / Modification Guide

- 입력 해석 변경 → `input.resolve_llm_target` (stub과 분리 유지).
- LLM 호출·메시지 조립 → `llm_runner.py` (테스트에서 `llm=` mock 주입).
- 상태 갱신·recursion_depth 증가 → `apply.apply_deconstruct_result`.
- 노드 시그니처 `(state: State) -> dict` 유지 — LangGraph partial state update 규약.
"""

from __future__ import annotations

from deconstructor.deconstruct.apply import apply_deconstruct_result
from deconstructor.deconstruct.input import resolve_llm_target
from deconstructor.deconstruct.llm_runner import invoke_fact_list
from deconstructor.pipeline.state import State
from deconstructor.web.progress_ctx import progress_sub


def deconstruct_node(state: State) -> dict:
    """
    Split input via LLM with structured FactList output.

    LLM으로 입력을 분해하고 구조화된 FactList를 State에 반영한다.
    대상이 없으면 빈 dict 반환(상태 무변경).
    """
    # LLM 경로: subject|state_change 조합 또는 초기 raw_text
    target = resolve_llm_target(state)
    if target is None:
        # pending 비었고 recursion_depth>0 → 더 이상 분해할 crumb 없음
        return {}

    # R12-2: structured output FactList
    with progress_sub("LLM", "Gemini FactList 호출", f"{len(target.text)}자"):
        result = invoke_fact_list(target.text)

    # parent_id 있으면 해당 crumb를 children으로 교체; depth +1
    return apply_deconstruct_result(
        pending=state["extracted_facts"],
        parent_id=target.parent_id,
        result=result,
        recursion_depth=state["recursion_depth"],
    )
