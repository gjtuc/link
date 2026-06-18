"""Trace detail fragment for recursion_depth increments.
recursion_depth 증가 update용 trace detail 조각.

Purpose / 목적
--------------
Shows ``depth->N`` when deconstruct loop bumps ``recursion_depth`` in state.
deconstruct 루프가 ``recursion_depth``를 올릴 때 ``depth->N`` 표시.

Pipeline position / 파이프라인 위치
-----------------------------------
Mid-order in ``DETAIL_HANDLERS``; correlates with deconstruct node revisits.
``DETAIL_HANDLERS`` 중간; deconstruct 재방문과 연관.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Only fires when ``recursion_depth`` key in update (not every node touches it).
- ``recursion_depth`` 키가 update에 있을 때만 발화.
"""

from __future__ import annotations

from typing import Any


def detail_recursion_depth(update: dict[str, Any]) -> str | None:
    """Format recursion_depth change for trace detail."""
    if "recursion_depth" not in update:
        return None
    return f"depth->{update['recursion_depth']}"
