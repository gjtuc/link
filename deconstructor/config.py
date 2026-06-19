"""
런타임 설정 로더 — LLM·Neo4j·파이프라인 상수
=============================================

## 로드 순서 (우선순위 높은 것이 나중에 덮어씀)

  1. 이 파일의 기본값
  2. 프로젝트 루트 `.env` (python-dotenv)
  3. `deconstructor/local_settings.py` (gitignore, 개발 PC별 비밀키)

## 다른 AI가 수정할 때

  - 새 환경 변수 추가: 여기에 기본값 + `_apply_local_settings()` 목록에 이름 추가
  - `local_settings.example.py`에도 동일 키 예시 추가 (실제 키는 넣지 말 것)
  - `resolve_llm_provider()`: auto 시 Gemini 키 우선 → OpenAI 순

## 보안

  `local_settings.py`는 절대 커밋하지 않음. 로그에 키 출력 금지.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# deconstructor/ 패키지의 부모 = 프로젝트 루트 (requirements.txt, main.py 위치)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _first_env(*names: str) -> str:
    """여러 env 이름 중 첫 번째 비어 있지 않은 값 (Gemini 키 별칭 호환)."""
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""


# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Google Gemini (여러 env 이름 지원) ---
GEMINI_API_KEY = _first_env(
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
)
# gemini-2.0-flash 는 일부 계정에서 404 — 3.x Flash/Pro 권장 (README 참고)
GEMINI_MODEL_FLASH = os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash")
GEMINI_MODEL_PRO = os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview")
# 하위 호환: GEMINI_MODEL 단일 지정 시 Flash 로 취급
GEMINI_MODEL = os.getenv("GEMINI_MODEL", GEMINI_MODEL_FLASH)

# Gemini 3+ thinking_level: minimal | low | medium | high
GEMINI_THINKING_LEVEL_FLASH = os.getenv("GEMINI_THINKING_LEVEL_FLASH", "medium")
GEMINI_THINKING_LEVEL_PRO = os.getenv("GEMINI_THINKING_LEVEL_PRO", "high")

# auto | gemini | openai
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()

# --- Neo4j (로컬 Desktop 기본 bolt) ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# deconstruct ↔ verify 루프 최대 반복 (routing/after_verify.py 와 연동)
MAX_DECOMPOSITION_ITERATIONS = int(os.getenv("MAX_DECOMPOSITION_ITERATIONS", "5"))

# --- Tavily (Fact-Checker live search) ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def _apply_local_settings() -> None:
    """
    `deconstructor/local_settings.py` 가 있으면 모듈 상수를 덮어씀.

    ImportError면 무시 (CI·테스트는 env만 사용 가능).
    """
    global OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, GEMINI_MODEL
    global GEMINI_MODEL_FLASH, GEMINI_MODEL_PRO
    global GEMINI_THINKING_LEVEL_FLASH, GEMINI_THINKING_LEVEL_PRO
    global LLM_PROVIDER, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, TAVILY_API_KEY

    try:
        from deconstructor import local_settings as local
    except ImportError:
        return

    for name in (
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_MODEL_FLASH",
        "GEMINI_MODEL_PRO",
        "GEMINI_THINKING_LEVEL_FLASH",
        "GEMINI_THINKING_LEVEL_PRO",
        "LLM_PROVIDER",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "TAVILY_API_KEY",
    ):
        value = getattr(local, name, None)
        if value:
            globals()[name] = value


# import 시점에 한 번 적용 (모듈 캐시 후 변경은 반영 안 됨 — 재시작 필요)
_apply_local_settings()


def resolve_llm_provider() -> str:
    """
    사용할 LLM 백엔드 결정.

    Returns:
        "gemini" | "openai" | "" (키 없음)

    수정 시: llm/__init__.py 의 get_chat_model() 과 함께 테스트.
    """
    if LLM_PROVIDER in ("gemini", "openai"):
        return LLM_PROVIDER
    if GEMINI_API_KEY:
        return "gemini"
    if OPENAI_API_KEY:
        return "openai"
    return ""
