"""Registry of per-field trace detail handlers for stream updates.
stream update용 필드별 trace detail 핸들러 레지스트리.

Purpose / 목적
--------------
Central **open-closed** registry: each State field that should appear in trace
``detail`` has a small ``detail_*`` function; count extractors exposed as
``COUNT_*`` aliases for ``StepRecord`` numeric fields.
trace ``detail``에 넣을 State 필드마다 ``detail_*`` 함수 등록;
카운트 추출기는 ``COUNT_*``로 ``StepRecord`` 숫자 필드에 연결.

Pipeline position / 파이프라인 위치
-----------------------------------
Imported by ``summarize/compose.py`` only (handlers should not import compose).
``summarize/compose.py``만 import (handler → compose 역방향 금지).

Handler order / 핸들러 순서
---------------------------
extracted → completed → edges → depth → partial → weaver
(mirrors typical node write order in a deconstruct cycle).

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
1. Create ``handlers/<topic>.py`` with ``detail_*`` and optional ``count_*``.
2. Append to ``DETAIL_HANDLERS`` tuple in stable order.
3. Export count function as ``COUNT_*`` if ``StepRecord`` needs it.
4. Handlers must return ``None`` when key absent — never raise on missing keys.
5. handler 파일 추가 → ``DETAIL_HANDLERS`` 등록 → 필요 시 ``COUNT_*``.
6. 키 없으면 ``None`` — missing key 예외 금지.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from deconstructor.pipeline.trace.summarize.handlers.completed import (
    count_completed_facts,
    detail_completed_facts,
)
from deconstructor.pipeline.trace.summarize.handlers.depth import detail_recursion_depth
from deconstructor.pipeline.trace.summarize.handlers.edges import (
    count_verified_edges,
    detail_verified_edges,
)
from deconstructor.pipeline.trace.summarize.handlers.extracted import (
    count_extracted_facts,
    detail_extracted_facts,
)
from deconstructor.pipeline.trace.summarize.handlers.partial import detail_partial_run
from deconstructor.pipeline.trace.summarize.handlers.weaver import detail_weaver_result

DetailFn = Callable[[dict[str, Any]], str | None]

DETAIL_HANDLERS: tuple[DetailFn, ...] = (
    detail_extracted_facts,
    detail_completed_facts,
    detail_verified_edges,
    detail_recursion_depth,
    detail_partial_run,
    detail_weaver_result,
)

COUNT_EXTRACTED = count_extracted_facts
COUNT_COMPLETED = count_completed_facts
COUNT_VERIFIED = count_verified_edges
