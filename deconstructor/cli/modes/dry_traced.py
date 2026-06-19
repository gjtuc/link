"""
dry_traced — dry-run traced 파이프라인 CLI 모드
===============================================

## 목적 / Purpose

LLM 없이 stub deconstruct로 파이프라인을 실행하고, **단계별 trace**가 포함된 리포트 또는
JSON State를 출력한다. `--dry-run`, `--depth-cap` 경로에서 사용된다.

Runs the pipeline with stub deconstruct (no LLM) and prints a **step-by-step traced**
report or JSON State. Used for `--dry-run` and `--depth-cap` paths.

## 파이프라인 위치 / Pipeline Position

::

    dispatch(dry_run) → run_dry_traced → pipeline_trace.run_pipeline_traced
                                              ↓
                                    format_traced_report | state_to_json

`graph.run_pipeline`과 별도 — trace 수집이 목적.

Separate from `graph.run_pipeline` — purpose is trace collection.

## 수정 가이드 / Modification Guide

- `max_recursion_depth=cap` — `headline.resolve_headline`의 cap과 연동.
- `persist_db` — dry-run에서도 `--db` 시 Neo4j weaver 가능.
- 리포트 포맷 → `report.format_traced_report`; live는 `format_dry_run_report` (이름 주의).
"""

from __future__ import annotations

from deconstructor.cli.print_util import safe_print
from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.report import format_traced_report, state_to_json


def run_dry_traced(
    headline: str,
    *,
    cap: int | None,
    persist_db: bool,
    as_json: bool,
) -> int:
    traced = run_pipeline_traced(
        headline,
        dry_run=True,
        max_recursion_depth=cap,
        persist_db=persist_db,
    )
    if as_json:
        safe_print(state_to_json(traced.final_state))
        return 0
    safe_print(format_traced_report(traced))
    return 0
