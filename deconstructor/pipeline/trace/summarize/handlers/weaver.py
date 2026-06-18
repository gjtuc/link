"""Trace detail fragment for weaver_result field updates.
weaver_result 필드 update용 trace detail 조각.

Purpose / 목적
--------------
When a node update includes ``weaver_result``, append compact summary:
mode, nodes_written, edges_written for the PIPELINE TRACE line.
노드 update에 ``weaver_result``가 있으면 mode·nodes·edges 요약을 detail에 추가.

Pipeline position / 파이프라인 위치
-----------------------------------
Last handler in ``DETAIL_HANDLERS`` — typically final weaver node.
``DETAIL_HANDLERS`` **마지막** — 보통 최종 weaver 노드.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Match fields shown in ``report.sections.weaver`` for operator consistency.
- Return ``None`` if key missing or value ``None``.
- ``report.sections.weaver``와 필드 표기 일치.
"""

from __future__ import annotations

from typing import Any


def detail_weaver_result(update: dict[str, Any]) -> str | None:
    """Format weaver_result sub-dict entry for trace detail string."""
    wr = update.get("weaver_result")
    if wr is None:
        return None
    return f"weaver={wr.mode} nodes={wr.nodes_written} edges={wr.edges_written}"
