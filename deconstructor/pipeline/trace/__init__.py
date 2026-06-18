"""Pipeline execution trace — public API for traced runs.
파이프라인 실행 추적 — traced run 공개 API.

Purpose / 목적
--------------
Re-exports ``run_pipeline_traced``, ``TracedRun``, ``StepRecord``, and
``summarize_update`` — the observability layer over LangGraph ``stream(updates)``.
LangGraph ``stream(updates)`` 위 관측 계층의 진입점 재노출.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    build_graph() --> run_pipeline_traced() --> TracedRun
                          |
                          +--> summarize_update (per chunk)

Canonical import path (prefer over ``deconstructor.pipeline_trace`` shim).
정식 import 경로 (``pipeline_trace`` shim 보다 우선).

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Implement tracing in ``trace/runner.py`` and ``trace/summarize/``.
- Add new detail handlers under ``trace/summarize/handlers/`` and register in
  ``handlers/__init__.py`` — do not grow runner.py with field-specific logic.
- runner·핸들러 분리 유지; runner에 필드별 로직 비대화 금지.
"""

from deconstructor.pipeline.trace.runner import run_pipeline_traced
from deconstructor.pipeline.trace.summarize import summarize_update
from deconstructor.pipeline.trace.types import StepRecord, TracedRun

__all__ = ["StepRecord", "TracedRun", "run_pipeline_traced", "summarize_update"]
