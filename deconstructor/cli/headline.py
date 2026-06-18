"""
headline — CLI 헤드라인·depth cap 해석
========================================

## 목적 / Purpose

CLI 인자와 dry-run/live 모드에 따라 **입력 헤드라인 문자열**과
**max_recursion_depth cap**(depth-cap 시나리오용)을 결정한다.

Resolves **input headline string** and **max_recursion_depth cap** (for depth-cap
scenarios) from CLI args and dry-run/live mode.

## 파이프라인 위치 / Pipeline Position

::

    dispatch → resolve_headline(args, dry_run) → (headline, cap)
                    ↓
         run_dry_traced(..., cap=cap) / run_live(headline)

cap은 dry-run traced 경로에서만 `run_pipeline_traced`에 전달된다.

`cap` is passed to `run_pipeline_traced` only on the dry-run traced path.

## 수정 가이드 / Modification Guide

- 시나리오 상수 → `dry_run/scenarios.py` (`DEFAULT_HEADLINE`, `DEPTH_CAP_SCENARIO`).
- `is_depth_cap_headline` 휴리스틱 변경 시 `--depth-cap` 플래그 없이도 cap 적용 가능.
- `LIVE_DEFAULT_HEADLINE`은 live 모드 전용 기본값 — 문서·데모와 동기화.
"""

from __future__ import annotations

import argparse

from deconstructor.dry_run.modes import is_depth_cap_headline
from deconstructor.dry_run.scenarios import DEFAULT_HEADLINE, DEPTH_CAP_SCENARIO

LIVE_DEFAULT_HEADLINE = "Factory A loses grid power for 4 hours."


def resolve_headline(
    args: argparse.Namespace,
    *,
    dry_run: bool,
) -> tuple[str, int | None]:
    if args.depth_cap:
        # 명시적 depth-cap 시나리오 헤드라인
        headline = args.event or DEPTH_CAP_SCENARIO.headline
    elif dry_run:
        headline = args.event or DEFAULT_HEADLINE
    else:
        headline = args.event or LIVE_DEFAULT_HEADLINE

    # depth-cap 플래그 또는 헤드라인 휴리스틱 → recursion 상한
    cap = (
        DEPTH_CAP_SCENARIO.max_recursion_depth
        if args.depth_cap or is_depth_cap_headline(headline)
        else None
    )
    return headline, cap
