"""Backward-compatible re-export for report formatting API.
하위 호환용 리포트 포맷 API 재보내기.

Purpose / 목적
--------------
Centralizes **human-readable report** and **JSON export** entry points for
callers that still import from ``deconstructor.report`` (legacy path).
**사람이 읽는 리포트** 및 **JSON보내기** 진입점을 레거시 경로
``deconstructor.report`` import 에 맞춰 한곳에 모읍니다.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    State or TracedRun
        -> format_dry_run_report / format_traced_report  [report.compose]
        -> format_step_trace                           [report.sections.trace]
        -> state_to_json                                 [report.json_export]
        -> str (console) or file write (CLI)

Reporting is the **terminal presentation layer**: it reads final (or mid-run)
``State`` and optional ``StepRecord`` list; it never mutates pipeline data.
리포트는 **최종 표현 계층**입니다. ``State``와 선택적 ``StepRecord`` 목록을
읽기만 하며 파이프라인 데이터를 변경하지 않습니다.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- **Do not** implement section logic here. Add sections under
  ``deconstructor/report/sections/`` and wire them in ``report/compose.py``.
- Keep ``__all__`` in sync with ``report/__init__.py`` for public API parity.
- Prefer importing from ``deconstructor.report`` package in new code; this
  root ``report.py`` exists only for import-path stability.
- **섹션 로직은 여기 두지 말 것.** ``report/sections/`` + ``compose.py`` 연결.
- 공개 API는 ``report/__init__.py``와 ``__all__`` 동기화.
- 신규 코드는 ``deconstructor.report`` 패키지 import 권장; 루트 ``report.py``는
  import 경로 안정성용.
"""

from deconstructor.report.compose import format_dry_run_report, format_traced_report
from deconstructor.report.json_export import state_to_json
from deconstructor.report.sections.trace import format_step_trace

__all__ = [
    "format_dry_run_report",
    "format_step_trace",
    "format_traced_report",
    "state_to_json",
]
