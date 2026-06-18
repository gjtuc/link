"""
deconstruct_node_stub — dry-run 결정론적 분해 LangGraph 노드
============================================================

## 목적 / Purpose

LLM 없이 `dry_run.stub.stub_decompose`로 고정된 `FactList`를 생성해 파이프라인 전체
(deconstruct → verify → skeptic → weaver)를 **비용·네트워크 없이** 검증한다.

Produces deterministic `FactList` via `dry_run.stub.stub_decompose` without an LLM,
enabling full pipeline smoke tests (deconstruct → verify → skeptic → weaver) at zero
API cost.

## 파이프라인 위치 / Pipeline Position

::

    build_graph(dry_run=True) → deconstruct_node_stub (replaces deconstruct_node)

`graph/builder.py`에서 `dry_run=True`일 때 `deconstruct` 노드에 바인딩된다.
CLI `--dry-run` / `--depth-cap` 경로와 `pipeline_trace`가 이 노드를 사용한다.

Bound to the `deconstruct` node when `dry_run=True` in `graph/builder.py`.
Used by CLI `--dry-run` / `--depth-cap` and `pipeline_trace`.

## 수정 가이드 / Modification Guide

- 스텁 분해 로직 → `dry_run/stub.py` (`stub_decompose`); 여기는 LangGraph 어댑터만 유지.
- 입력 해석 → `input.resolve_stub_target` (LLM 경로 `resolve_llm_target`과 별도).
- 시나리오·헤드라인 → `dry_run/scenarios.py`, `cli/headline.py`.
- live 노드(`node.py`)와 동일하게 `apply_deconstruct_result`로 상태 병합.
"""

from __future__ import annotations

from deconstructor.deconstruct.apply import apply_deconstruct_result
from deconstructor.deconstruct.input import resolve_stub_target
from deconstructor.dry_run.stub import stub_decompose
from deconstructor.pipeline.state import State


def deconstruct_node_stub(state: State) -> dict:
    """
    Deterministic stub — no LLM.

    결정론적 스텁 분해; API 호출 없음. refining 플래그는 stub_decompose 시나리오 제어용.
    """
    # 스텁 전용: 항상 raw_text 기준, parent_id는 pending[0] (있을 때)
    target = resolve_stub_target(state)
    if target is None:
        return {}

    # dry_run 패키지의 고정 FactList 생성
    result = stub_decompose(target.text, refining=target.refining)
    return apply_deconstruct_result(
        pending=state["extracted_facts"],
        parent_id=target.parent_id,
        result=result,
        recursion_depth=state["recursion_depth"],
    )
