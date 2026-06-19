"""
llm_runner — deconstruct 전용 LLM 호출 격리 계층
================================================

## 목적 / Purpose

Deconstruct 노드의 LLM 의존성을 한 파일에 모아 **단위 테스트에서 mock 주입**이 가능하게 한다.
시스템/유저 프롬프트 조립과 `FactList` structured output 호출만 담당한다.

Isolates LLM dependency for the deconstruct node so unit tests can inject mocks.
Handles message assembly and `FactList` structured-output invocation only.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct/node.py → llm_runner.invoke_fact_list → llm.get_chat_model

verify·skeptic·weaver와 무관. deconstruct live 경로의 **유일한 LLM 호출 지점** (이 패키지 내).

Unrelated to verify/skeptic/weaver. The **sole LLM call site** within the deconstruct
package on the live path.

## 수정 가이드 / Modification Guide

- 프롬프트 문구 → `prompts.py` (여기서 import만).
- 모델·provider 변경 → `llm/get_chat_model()` 및 `config`; 이 파일은 `get_chat_model` 사용 유지.
- 출력 스키마 변경 → `models.FactList`와 프롬프트 동시 수정.
- 테스트: `invoke_fact_list(text, llm=FakeModel)` 패턴 사용 (R12-2).
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.deconstruct.prompts import DECONSTRUCT_SYSTEM, DECONSTRUCT_USER
from deconstructor.llm import get_chat_model
from deconstructor.models import FactList


def build_deconstruct_messages(text: str) -> list:
    """
    R12-1: assemble system + user messages.

    시스템 규칙(DECONSTRUCT_SYSTEM)과 사용자 입력 템플릿을 LangChain Message 리스트로 조립.
    """
    return [
        SystemMessage(content=DECONSTRUCT_SYSTEM),
        HumanMessage(content=DECONSTRUCT_USER.format(text=text)),
    ]


def invoke_fact_list(text: str, *, llm: Any | None = None) -> FactList:
    """
    R12-2: call LLM with structured FactList output.

    Pass ``llm`` in tests to inject a mock.

    기본: `get_chat_model(tier="flash")` + structured FactList (분해는 속도·비용용 Flash).
    테스트 시 `llm` 인자로 invoke 결과를 고정할 수 있다.
    """
    # 테스트 mock 우선; 없으면 Flash + Pydantic structured output
    model = (
        llm
        if llm is not None
        else get_chat_model(tier="flash").with_structured_output(FactList)
    )
    return model.invoke(build_deconstruct_messages(text))
