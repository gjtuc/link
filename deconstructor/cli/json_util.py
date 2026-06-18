"""
json_util — live 파이프라인 결과 JSON 인코딩
==============================================

## 목적 / Purpose

LangGraph 최종 State(및 중첩 nested Pydantic 모델)를 **UTF-8 JSON 문자열**로 직렬화한다.
`--json` live 모드에서 stdout 출력에 사용된다.

Serializes final LangGraph State (and nested Pydantic models) to a **UTF-8 JSON string**.
Used for stdout output in live `--json` mode.

## 파이프라인 위치 / Pipeline Position

::

    run_live(as_json=True) → encode_pipeline_result(result) → print

dry-run traced JSON은 `report.state_to_json` 사용 — 경로별 encoder 분리 유지.

Dry-run traced JSON uses `report.state_to_json` — keep encoders separate per path.

## 수정 가이드 / Modification Guide

- `default=` lambda: `model_dump(mode="json")` — Pydantic v2 규약.
- `ensure_ascii=False` — 한글 헤드라인·fact subject 보존.
- datetime 등 비표준 타입 추가 시 default handler 확장.
"""

from __future__ import annotations

import json
from typing import Any


def encode_pipeline_result(result: Any) -> str:
    # Pydantic 모델은 model_dump; 그 외는 json 기본 직렬화
    return json.dumps(
        result,
        default=lambda o: o.model_dump(mode="json") if hasattr(o, "model_dump") else o,
        ensure_ascii=False,
        indent=2,
    )
