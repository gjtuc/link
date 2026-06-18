"""
gemini_provider — Google Gemini Chat 모델 팩토리
================================================

## 목적 / Purpose

`ChatGoogleGenerativeAI` 인스턴스를 `config.GEMINI_MODEL`·`GEMINI_API_KEY`로
구성한다. `get_chat_model()`에서 provider=="gemini"일 때 호출된다.

Constructs a `ChatGoogleGenerativeAI` instance from `config.GEMINI_MODEL` and
`GEMINI_API_KEY`. Called by `get_chat_model()` when provider=="gemini".

## 파이프라인 위치 / Pipeline Position

::

    llm.get_chat_model → build_gemini_model → LangChain invoke

OpenAI provider와 **대칭** — 한쪽만 수정하지 말 것.

Symmetric with OpenAI provider — keep both in sync when changing patterns.

## 수정 가이드 / Modification Guide

- 모델명 기본값 → `config.GEMINI_MODEL` (local_settings.example 참고).
- 키 누락 시 명확한 RuntimeError 메시지 유지.
- langchain-google-genai 버전 업 시 import 경로·인자명 변경 확인.
"""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from deconstructor import config


def build_gemini_model():
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Use .env or deconstructor/local_settings.py"
        )
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0,
    )
