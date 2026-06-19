"""
dispatch — CLI 실행 모드 분기
==============================

## 목적 / Purpose

파싱된 argv를 기준으로 **skeptic-only 데모**, **dry-run traced**, **live LLM**
파이프라인 중 하나를 실행하고 종료 코드를 반환한다.

Runs one of **skeptic-only demo**, **dry-run traced**, or **live LLM** pipeline
based on parsed argv and returns an exit code.

## 파이프라인 위치 / Pipeline Position

::

    build_parser().parse_args → dispatch → run_* / skeptic_demo

`deconstructor` 패키지 `__main__` 또는 테스트에서 `dispatch(argv)` 호출.

Invoked from package `__main__` or tests via `dispatch(argv)`.

## 수정 가이드 / Modification Guide

- `dry_run = args.dry_run or args.depth_cap` — depth-cap 시나리오도 stub 경로.
- 새 모드 추가 시 early return 패턴 유지 (`skeptic_only` 참고).
- `resolve_headline`과 cap 전달 일관성 — `modes/dry_traced.py`의 `max_recursion_depth`.
"""

from __future__ import annotations

from deconstructor.cli.headline import resolve_headline
from deconstructor.cli.modes import run_dry_traced, run_live
from deconstructor.cli.parser import build_parser
from deconstructor.cli.skeptic_demo import run_skeptic_demo


def dispatch(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # 독립 데모: 전체 파이프라인 없이 SkepticEngine만 실행
    if args.skeptic_only:
        print(run_skeptic_demo())
        return 0

    # --dry-run 또는 --depth-cap → stub deconstruct 경로
    dry_run = args.dry_run or args.depth_cap
    headline, cap = resolve_headline(args, dry_run=dry_run)

    if dry_run and not args.enable_dreamer:
        return run_dry_traced(
            headline,
            cap=cap,
            persist_db=args.db,
            as_json=args.json,
        )

    return run_live(
        headline,
        persist_db=args.db,
        as_json=args.json,
        dry_run=dry_run,
        enable_dreamer=args.enable_dreamer,
    )
