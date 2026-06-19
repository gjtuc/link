"""
llm 패키지 — Chat 모델 provider 디스패치
========================================

## 목적 / Purpose

`config.resolve_llm_provider()` 결과에 따라 **Gemini** 또는 **OpenAI** LangChain chat
모델을 생성한다. deconstruct·skeptic live 경로의 공통 LLM 진입점.

Builds **Gemini** or **OpenAI** LangChain chat models based on
`config.resolve_llm_provider()`. Common LLM entry point for deconstruct/skeptic live paths.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct/llm_runner → get_chat_model()
    skeptic (live)       → get_chat_model()

API 키 미설정 시 `RuntimeError` — CLI live 모드 시작 전 `.env` / `local_settings.py` 확인.

Raises `RuntimeError` if no API key — verify `.env` / `local_settings.py` before live CLI.

## 수정 가이드 / Modification Guide

- 새 provider 추가: `*_provider.py` + `get_chat_model` 분기 + `config` 키.
- temperature=0 고정 — 창의적 변형 방지; 변경 시 전 파이프라인 회귀 테스트.
- structured output은 호출부(`with_structured_output`)에서 래핑.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from deconstructor import config
from deconstructor.llm.gemini_provider import GeminiTier, build_gemini_model
from deconstructor.llm.openai_provider import build_openai_model


def get_chat_model(*, tier: GeminiTier = "pro") -> BaseChatModel:
    """
    LLM 인스턴스 반환.

    tier=pro   — Deconstruct·Skeptic·긴 문서 요약 (Gemini 3.1 Pro, thinking high)
    tier=flash — 이미지 OCR·가벼운 추출 (Gemini 3.5 Flash)
    """
    provider = config.resolve_llm_provider()
    if provider == "gemini":
        return build_gemini_model(tier=tier)
    if provider == "openai":
        return build_openai_model()
    raise RuntimeError(
        "No LLM API key configured. Set GEMINI_API_KEY or OPENAI_API_KEY in "
        ".env or deconstructor/local_settings.py (see local_settings.example.py)."
    )
