"""
cli 패키지 — deconstructor 명령줄 진입점
=========================================

## 목적 / Purpose

argparse 파싱, 실행 모드 분기(dry-run traced / live LLM / skeptic-only demo),
헤드라인·depth cap 해석, Windows 안전 출력을 제공한다.

Provides argparse parsing, execution mode dispatch (dry-run traced / live LLM /
skeptic-only demo), headline/depth-cap resolution, and Windows-safe printing.

## 파이프라인 위치 / Pipeline Position

::

    __main__ / entrypoint → dispatch → run_dry_traced | run_live | skeptic_demo
                              ↓
                    graph.build_graph / pipeline_trace

사용자-facing **최상위 UI**; LangGraph 노드 로직은 포함하지 않는다.

User-facing **top-level UI**; does not contain LangGraph node logic.

## 수정 가이드 / Modification Guide

- 새 CLI 플래그 → `parser.py` + `dispatch.py` 분기 + 해당 mode 모듈.
- 기본 헤드라인 → `headline.py` (`LIVE_DEFAULT_HEADLINE`, dry_run scenarios).
- JSON 출력 → `json_util.encode_pipeline_result` 또는 `report.state_to_json`.
- cp949 터미널 → `print_util.safe_print` 사용.
"""

from deconstructor.cli.dispatch import dispatch
from deconstructor.cli.headline import LIVE_DEFAULT_HEADLINE, resolve_headline
from deconstructor.cli.json_util import encode_pipeline_result
from deconstructor.cli.modes import run_dry_traced, run_live
from deconstructor.cli.parser import build_parser
from deconstructor.cli.print_util import safe_print

__all__ = [
    "LIVE_DEFAULT_HEADLINE",
    "build_parser",
    "dispatch",
    "encode_pipeline_result",
    "resolve_headline",
    "run_dry_traced",
    "run_live",
    "safe_print",
]
