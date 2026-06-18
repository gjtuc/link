"""Trace detail and count helpers for extracted_facts queue updates.
extracted_facts 큐 update용 trace detail·카운트 헬퍼.

Purpose / 목적
--------------
First handler in registry. Summarizes deconstruct output: total extracted count
and how many remain non-atomic (drive loop-back to deconstruct).
레지스트리 첫 핸들러. deconstruct 출력: 추출 수 + 비원자 개수(루프백 신호).

Pipeline position / 파이프라인 위치
-----------------------------------
Fires on deconstruct node updates; ``non_atomic`` hints verify routing.
deconstruct 노드 update; ``non_atomic``은 verify 라우팅 힌트.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``non_atomic`` uses ``f.is_atomic`` on ``AtomicFact`` models in update list.
- Do not import deconstruct logic — read only the update dict.
- ``AtomicFact.is_atomic``만 참조; deconstruct 로직 import 금지.
"""

from __future__ import annotations

from typing import Any


def detail_extracted_facts(update: dict[str, Any]) -> str | None:
    """Summarize extracted fact queue size and non-atomic subset."""
    if "extracted_facts" not in update:
        return None
    facts = update["extracted_facts"]
    non_atomic = sum(1 for f in facts if not f.is_atomic)
    return f"extracted={len(facts)} non_atomic={non_atomic}"


def count_extracted_facts(update: dict[str, Any]) -> int | None:
    """Queue length for StepRecord.extracted_count."""
    if "extracted_facts" not in update:
        return None
    return len(update["extracted_facts"])
