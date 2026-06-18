"""Rejected hypotheses section — skeptic rule failures.
기각된 가설 섹션 — 스켉틱 규칙 실패.

Purpose / 목적
--------------
Summarizes ``state['rejected_hypotheses']`` with classification, fact id
prefixes, failed rule ids, and reason text. Truncates display to ``limit``
entries to keep reports readable on noisy runs.
``state['rejected_hypotheses']`` 요약: 분류·팩트 id 접두·실패 규칙·사유.
``limit``개만 표시해 장문 실행 리포트 가독성 유지.

Pipeline position / 파이프라인 위치
-----------------------------------
After verified edges in ``compose``; data produced by skeptic node.
``compose``에서 verified edges 다음; skeptic 노드 산출.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``limit`` is a keyword-only param for tests that need full dump — default 8.
- Do not sort here unless product requires stable ordering (graph order preserved).
- 전체 덤프 테스트는 ``limit`` 조정; 기본 8.
- 정렬 추가는 제품 요구 시만 (현재 그래프 순서 유지).
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_rejected_section(state: State, *, limit: int = 8) -> list[str]:
    """Format rejected hypotheses; tail ellipsis when count exceeds limit."""
    rejected = state["rejected_hypotheses"]
    lines = [f"--- REJECTED HYPOTHESES ({len(rejected)}) ---"]
    for rej in rejected[:limit]:
        lines.append(
            f"  [{rej.classification.value}] "
            f"{rej.source_fact_id[:8]}.. -> {rej.target_fact_id[:8]}.. "
            f"rules={','.join(rej.failed_rule_ids) or '-'} "
            f"({rej.reason})"
        )
    if len(rejected) > limit:
        lines.append(f"  ... and {len(rejected) - limit} more")
    return lines
