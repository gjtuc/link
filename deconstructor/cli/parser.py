"""
parser — CLI argparse 정의
==========================

## 목적 / Purpose

`deconstructor` 실행 시 사용할 **명령줄 인자 스키마**를 정의한다.
event 위치 인자, JSON 출력, dry-run, depth cap, Neo4j, skeptic-only 플래그.

Defines the **command-line argument schema** for running `deconstructor`:
positional event, JSON output, dry-run, depth cap, Neo4j, skeptic-only flags.

## 파이프라인 위치 / Pipeline Position

::

    dispatch → build_parser().parse_args(argv)

플래그 의미 해석은 `dispatch.py`·`headline.py`·`modes/`가 담당.

Flag semantics interpreted by `dispatch.py`, `headline.py`, and `modes/`.

## 수정 가이드 / Modification Guide

- `nargs="?"` event — 생략 시 mode별 기본 헤드라인(`headline.py`).
- `--db` help 문구와 `weaver/neo4j_store` 동작 일치 유지.
- breaking CLI 변경 시 README·스모크 테스트 argv 갱신.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deconstruct an event into atomic facts and verify causality.",
    )
    # 선택적 이벤트 텍스트 — 없으면 mode별 DEFAULT
    parser.add_argument("event", nargs="?", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stub decomposer, no LLM (weaver still runs in console mode).",
    )
    parser.add_argument("--depth-cap", action="store_true")
    parser.add_argument(
        "--db",
        action="store_true",
        help="Persist verified edges to Neo4j (default: --no-db console weaver).",
    )
    parser.add_argument(
        "--enable-dreamer",
        action="store_true",
        help="Run Dreamer + Fact-Checker after decompose (requires more API usage live).",
    )
    parser.add_argument("--skeptic-only", action="store_true")
    return parser
