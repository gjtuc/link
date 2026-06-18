"""
cli.modes 패키지 — 파이프라인 실행 모드 구현
============================================

## 목적 / Purpose

dry-run traced(`run_dry_traced`)와 live LLM(`run_live`) 두 가지 **end-to-end CLI 실행기**를
export한다. 각각 다른 파이프라인 진입점·리포트 포맷을 사용한다.

Exports two **end-to-end CLI runners**: dry-run traced (`run_dry_traced`) and live LLM
(`run_live`). Each uses a different pipeline entry point and report format.

## 파이프라인 위치 / Pipeline Position

::

    dispatch → modes.run_dry_traced | modes.run_live

## 수정 가이드 / Modification Guide

- 새 모드 파일 추가 후 여기 `__all__` 및 `dispatch.py` 분기 연결.
- viz 후처리 `maybe_visualize_after_pipeline` — 두 모드 모두 동일 호출 패턴 유지.
"""

from deconstructor.cli.modes.dry_traced import run_dry_traced
from deconstructor.cli.modes.live import run_live

__all__ = ["run_dry_traced", "run_live"]
