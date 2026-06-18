"""
skeptic_demo — skeptic-only 내장 데모 facts
===========================================

## 목적 / Purpose

`--skeptic-only` 플래그 시 전체 LangGraph 없이 **고정 grid→motor fact 쌍**으로
`SkepticEngine.evaluate_batch`를 실행하고 JSON 문자열을 반환한다.

On `--skeptic-only`, runs `SkepticEngine.evaluate_batch` on a **fixed grid→motor fact
pair** without the full LangGraph and returns a JSON string.

## 파이프라인 위치 / Pipeline Position

::

    dispatch(skeptic_only=True) → run_skeptic_demo() → print

deconstruct·verify·weaver와 **독립** — skeptic 패키지 API 스모크용.

**Independent** of deconstruct/verify/weaver — smoke test for skeptic package API.

## 수정 가이드 / Modification Guide

- 데모 facts·타임스탬프 변경 시 JSON 스냅샷 테스트 갱신.
- `ensure_ascii=True` — 터미널 호환 우선(데모 전용).
- 엔진 규칙 변경은 `skeptic/` 패키지; 여기는 fixture 데이터만.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from deconstructor.models import AtomicFact
from deconstructor.skeptic import SkepticEngine


def run_skeptic_demo() -> str:
    """Evaluate a fixed grid→motor pair; return JSON string."""
    t0 = datetime(2026, 1, 1, 12, 0, 0)
    facts = [
        AtomicFact(
            id="f-grid",
            subject="grid",
            state_change="power -> off",
            timestamp=t0,
            is_atomic=True,
        ),
        AtomicFact(
            id="f-motor",
            subject="motor",
            state_change="power_supply -> interrupted",
            timestamp=t0 + timedelta(minutes=1),
            is_atomic=True,
        ),
    ]
    batch = SkepticEngine().evaluate_batch(facts)
    return json.dumps(batch.model_dump(mode="json"), ensure_ascii=True, indent=2)
