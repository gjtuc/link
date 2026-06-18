"""Trace detail fragment for partial_run flag updates.
partial_run 플래그 update용 trace detail 조각.

Purpose / 목적
--------------
Surfaces ``partial_run`` boolean in trace when graph sets depth-cap exhaustion.
그래프가 깊이 상한 partial_run을 설정할 때 trace에 boolean 노출.

Pipeline position / 파이프라인 위치
-----------------------------------
Registered before weaver handler; often appears on late deconstruct/verify steps.
weaver 핸들러 직전 등록; 후반 deconstruct/verify 단계에 자주 등장.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Uses ``"partial_run" not in update`` guard — key present with False still logs.
- Pair with ``pipeline.partial_run.REASON_DEPTH_CAP`` in report ``partial`` section.
- 키만 있으면 False도 로그; reason은 report partial 섹션 참고.
"""

from __future__ import annotations

from typing import Any


def detail_partial_run(update: dict[str, Any]) -> str | None:
    """Emit partial_run=true/false when key present in update."""
    if "partial_run" not in update:
        return None
    return f"partial_run={update['partial_run']}"
