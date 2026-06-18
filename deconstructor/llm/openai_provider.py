"""
openai_provider — OpenAI Chat 모델 팩토리
=========================================

## 목적 / Purpose

`ChatOpenAI` 인스턴스를 `config.OPENAI_MODEL`·`OPENAI_API_KEY`로 구성한다.
`get_chat_model()`에서 provider=="openai"일 때 호출된다.

Constructs a `ChatOpenAI` instance from `config.OPENAI_MODEL` and `OPENAI_API_KEY`.
Called by `get_chat_model()` when provider=="openai".

## 파이프라인 위치 / Pipeline Position

::

    llm.get_chat_model → build_openai_model → LangChain invoke

Gemini provider와 동일 temperature=0·에러 메시지 패턴 유지.

Keep temperature=0 and error-message pattern aligned with Gemini provider.

## 수정 가이드 / Modification Guide

- 모델명 → `config.OPENAI_MODEL`.
- Azure OpenAI 등 변형 필요 시 별도 provider 모듈 권장 (이 파일은 표준 OpenAI만).
- API 키는 config에서만 읽기 — 하드코딩 금지.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from deconstructor import config


def build_openai_model():
    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Use .env or deconstructor/local_settings.py"
        )
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0,
    )
