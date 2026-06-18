"""Backward-compatible re-export for pipeline trace API.
하위 호환용 파이프라인 추적 API 재보내기.

Purpose / 목적
--------------
This module is a **thin compatibility shim**. Older code and tests may import
``StepRecord``, ``TracedRun``, and ``run_pipeline_traced`` from
``deconstructor.pipeline_trace`` instead of ``deconstructor.pipeline.trace``.
이 모듈은 **얇은 호환 레이어**입니다. 기존 코드·테스트가
``deconstructor.pipeline.trace`` 대신 ``deconstructor.pipeline_trace``에서
추적 타입·실행 함수를 import 할 수 있게 합니다.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    CLI / tests
        -> run_pipeline_traced()   [deconstructor.pipeline.trace.runner]
        -> TracedRun.final_state
        -> format_traced_report()  [deconstructor.report.compose]

Trace capture happens **after** graph construction and **during** LangGraph
``stream(updates)``; this file does not run the pipeline itself.
추적은 그래프 구축 **이후**, LangGraph ``stream(updates)`` **도중**에 기록됩니다.
이 파일은 파이프라인을 직접 실행하지 않습니다.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- **Do not** add logic here. Implement in ``deconstructor/pipeline/trace/``.
- **Do not** remove this shim until all callers migrate to ``pipeline.trace``.
- When adding new trace exports, update ``pipeline/trace/__init__.py`` first,
  then mirror ``__all__`` here if backward compatibility is still required.
- **여기에 로직 추가 금지.** 구현은 ``deconstructor/pipeline/trace/``에.
- **모든 호출부가 ``pipeline.trace``로 이전될 때까지** 이 shim 제거 금지.
- 새 추적 export 추가 시 ``pipeline/trace/__init__.py`` 먼저 수정 후,
  하위 호환 필요 시 ``__all__``만 여기에 반영.
"""

# Re-export canonical implementations from the pipeline.trace package.
# pipeline.trace 패키지의 정식 구현을 그대로 재노출.
from deconstructor.pipeline.trace import StepRecord, TracedRun, run_pipeline_traced

__all__ = ["StepRecord", "TracedRun", "run_pipeline_traced"]
