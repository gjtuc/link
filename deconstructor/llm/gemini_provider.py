"""
gemini_provider — Google Gemini Chat 모델 팩토리 (Flash / Pro 이원화)
"""

from __future__ import annotations

from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI

from deconstructor import config

GeminiTier = Literal["flash", "pro"]


def _resolve_tier_model(tier: GeminiTier) -> tuple[str, str | None]:
    if tier == "flash":
        return config.GEMINI_MODEL_FLASH, config.GEMINI_THINKING_LEVEL_FLASH
    return config.GEMINI_MODEL_PRO, config.GEMINI_THINKING_LEVEL_PRO


def build_gemini_model(*, tier: GeminiTier = "pro") -> ChatGoogleGenerativeAI:
    """
    tier=flash  — gemini-3.5-flash: OCR·짧은 추출 (속도)
    tier=pro    — gemini-3.1-pro-preview: 분해·요약·검증 (thinking)
    """
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Use .env or deconstructor/local_settings.py"
        )
    model_name, thinking_level = _resolve_tier_model(tier)
    kwargs: dict = {
        "model": model_name,
        "google_api_key": config.GEMINI_API_KEY,
        "temperature": 0,
    }
    if thinking_level:
        kwargs["thinking_level"] = thinking_level
    return ChatGoogleGenerativeAI(**kwargs)
