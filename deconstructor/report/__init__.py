"""Report package public API — section formatters and composers.
리포트 패키지 공개 API — 섹션 포맷터 및 조립기.

Purpose / 목적
--------------
Aggregates every **report section formatter** and top-level composers so CLI,
tests, and notebooks can import a single namespace:
``format_dry_run_report``, ``state_to_json``, per-section helpers, etc.
CLI·테스트·노트북이 ``format_dry_run_report``, ``state_to_json``,
섹션별 헬퍼 등을 **단일 네임스페이스**에서 import 하도록 모읍니다.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    TracedRun or State  --->  compose.format_*_report  --->  str
                         --->  json_export.state_to_json --->  JSON str

Runs **after** pipeline execution (or dry-run). Each ``sections/*.py`` module
maps one slice of ``State`` to fixed-width console lines.
파이프라인(또는 dry-run) **실행 후** 동작. ``sections/*.py`` 각각이
``State``의 한 영역을 고정폭 콘솔 줄로 변환합니다.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
1. New report section: create ``sections/<name>.py`` with ``format_*_section``,
   add to ``compose.format_dry_run_report`` section order, export here in ``__all__``.
2. Section order in ``compose.py`` is user-visible — change only with intent.
3. Do not import LangGraph or LLM clients in this package (read-only views).
4. **새 섹션:** ``sections/<name>.py`` + ``compose.py`` 순서 + ``__all__`` 등록.
5. ``compose.py`` 섹션 순서는 사용자에게 보이므로 의도 없이 변경 금지.
6. LangGraph·LLM 클라이언트 import 금지 (읽기 전용 뷰만).
"""

from deconstructor.report.sections.atomic_facts import format_atomic_facts_section
from deconstructor.report.sections.edges import format_edges_section
from deconstructor.report.sections.footer import format_footer_section
from deconstructor.report.sections.header import format_header_section
from deconstructor.report.sections.partial import format_partial_run_section
from deconstructor.report.sections.rejected import format_rejected_section
from deconstructor.report.sections.remaining import format_remaining_section
from deconstructor.report.sections.skeptic_log import format_skeptic_log_section
from deconstructor.report.sections.status import format_status_line
from deconstructor.report.sections.trace import format_step_trace
from deconstructor.report.sections.weaver import format_weaver_section
from deconstructor.report.compose import format_dry_run_report, format_traced_report
from deconstructor.report.json_export import state_to_json

__all__ = [
    "format_atomic_facts_section",
    "format_dry_run_report",
    "format_edges_section",
    "format_footer_section",
    "format_header_section",
    "format_partial_run_section",
    "format_rejected_section",
    "format_remaining_section",
    "format_skeptic_log_section",
    "format_status_line",
    "format_step_trace",
    "format_traced_report",
    "format_weaver_section",
    "state_to_json",
]
