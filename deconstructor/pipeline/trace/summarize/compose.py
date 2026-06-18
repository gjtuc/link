"""Compose StepRecord from per-field trace detail handler registry.
필드별 trace detail 핸들러 레지스트리로 StepRecord 조립.

Purpose / 목적
--------------
``summarize_update`` iterates ``DETAIL_HANDLERS``, joins non-empty fragments
into ``detail`` string, and populates optional count fields via COUNT_* helpers.
``DETAIL_HANDLERS`` 순회 → ``detail`` 조립 + COUNT_*로 선택적 카운트 필드 설정.

Pipeline position / 파이프라인 위치
-----------------------------------
Between ``runner.py`` (raw update dict) and ``types.StepRecord``.
``runner.py`` raw update ↔ ``types.StepRecord`` 사이 어댑터.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Handler order affects ``detail`` fragment order in console trace — intentional.
- ``step_index`` placeholder 0 overwritten by runner.
- New State field in trace: add handler + register in ``handlers/__init__.py``.
- 핸들러 순서 = detail 조각 순서.
- trace에 새 State 필드 → handler + ``handlers/__init__.py`` 등록.
"""

from __future__ import annotations

from typing import Any

from deconstructor.pipeline.trace.summarize.handlers import (
    COUNT_COMPLETED,
    COUNT_EXTRACTED,
    COUNT_VERIFIED,
    DETAIL_HANDLERS,
)
from deconstructor.pipeline.trace.types import StepRecord


def summarize_update(node: str, update: dict[str, Any]) -> StepRecord:
    """Build StepRecord from one LangGraph node update dict."""
    detail_parts: list[str] = []
    for handler in DETAIL_HANDLERS:
        fragment = handler(update)
        if fragment:
            detail_parts.append(fragment)

    return StepRecord(
        step_index=0,  # runner assigns real 1-based index
        node=node,
        recursion_depth=update.get("recursion_depth"),
        extracted_count=COUNT_EXTRACTED(update),
        completed_count=COUNT_COMPLETED(update),
        verified_edge_count=COUNT_VERIFIED(update),
        detail="; ".join(detail_parts),
    )
