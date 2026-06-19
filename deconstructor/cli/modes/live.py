"""
live — live LLM 파이프라인 CLI 모드
====================================

## 목적 / Purpose

실제 LLM deconstruct·skeptic로 파이프라인을 1회 실행하고, 요약 리포트 또는 JSON
결과를 출력한다. API 키(`llm/`, `config`)가 필요하다.

Runs one full pipeline pass with real LLM deconstruct/skeptic and prints a summary
report or JSON result. Requires API keys (`llm/`, `config`).

## 파이프라인 위치 / Pipeline Position

::

    dispatch(live) → run_live → graph_builder.run_pipeline(dry_run=False)
                                      ↓
                            format_dry_run_report | encode_pipeline_result

기본 CLI 경로(`--dry-run` 없음).

Default CLI path when `--dry-run` is not set.

## 수정 가이드 / Modification Guide

- `run_pipeline` import — canonical은 `graph.builder`; shim `graph_builder`도 동작.
- JSON vs 텍스트: JSON은 `encode_pipeline_result`, 텍스트는 `safe_print` + 리포트.
- viz 후처리는 dry_traced와 동일 플래그 `persist_db`.
"""

from __future__ import annotations

from deconstructor.cli.json_util import encode_pipeline_result
from deconstructor.cli.print_util import safe_print
from deconstructor.graph_builder import run_pipeline
from deconstructor.report import format_dry_run_report


def run_live(
    headline: str,
    *,
    persist_db: bool,
    as_json: bool,
) -> int:
    result = run_pipeline(headline, dry_run=False, persist_db=persist_db)
    if as_json:
        print(encode_pipeline_result(result))
        return 0
    safe_print(format_dry_run_report(result))
    return 0
