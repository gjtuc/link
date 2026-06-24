"""
prompts — The Deconstructor LLM 프롬프트 상수
=============================================

## 목적 / Purpose

deconstruct live 경로에서 LLM에 전달하는 **시스템·사용자 프롬프트 문자열**을 정의한다.
출력은 반드시 `models.FactList` / `AtomicFact` Pydantic 스키마와 호환되어야 한다.

Defines **system and user prompt strings** for the deconstruct live path.
Output must remain compatible with `models.FactList` / `AtomicFact` Pydantic schemas.

## 파이프라인 위치 / Pipeline Position

::

    prompts → llm_runner.build_deconstruct_messages → LLM structured output

skeptic·weaver 프롬프트와 무관. deconstruct **단계 전용** 규칙(기계적 분해, 형용사 제거 등).

Unrelated to skeptic/weaver prompts. **Deconstruct-only** rules (mechanical split,
strip adjectives, etc.).

## 수정 가이드 / Modification Guide

- 스키마 필드 변경(`AtomicFact`, `FactList`) 시 프롬프트 예시·규칙 문구 동기화.
- `DECONSTRUCT_USER`의 `{text}` 플레이스홀더 유지 — `llm_runner`가 `.format(text=...)`.
- 온도·모델은 `llm/` 및 `config`; 여기서는 규칙 문장만 편집.
- 회귀 테스트: `tests/`에서 mock LLM 또는 스냅샷으로 FactList 품질 검증 권장.
"""

# 시스템: 역할·비협상 규칙 — 감정·예측·가치판단 금지
DECONSTRUCT_SYSTEM = """You are a mechanical text decomposer.

Rules (non-negotiable):
- Output ONLY physical subjects and observable state changes.
- Strip every adjective, emotion, forecast, and value judgment.
- Each fact: one subject + one state_change. No compound conditions.
- Set is_atomic=False if the fact combines multiple entities, causal steps, or clauses
  (e.g. subject contains "and", commas, or multiple events in state_change).
- Set is_atomic=True ONLY when ONE entity + ONE indivisible observable transition.
- reasoning must explain atomicity mechanically - never bullish/bearish/good/bad.
- timestamp: ISO-8601 datetime if the text implies when; otherwise null.
- For long document inputs: extract multiple distinct facts when supported (see user hint).
"""

# 사용자: 입력 텍스트 삽입 + JSON 스키마만 반환 지시
DECONSTRUCT_USER = """Decompose the input into a FactList.

Input:
{text}

Return structured JSON only. No prose outside the schema."""
