"""Skeptic log section — structured diagnostic entries.
스켉틱 로그 섹션 — 구조화된 진단 항목.

Purpose / 목적
--------------
Renders ``state.get('skeptic_log')`` — leveled log lines (info/warn/error)
emitted during skeptic evaluation for operator debugging.
``state.get('skeptic_log')`` 렌더 — 스켉틱 평가 중 기록된 level/code/message.

Pipeline position / 파이프라인 위치
-----------------------------------
After rejected hypotheses; optional field (defaults to empty list in factory).
rejected 다음; 선택 필드 (factory 기본 빈 리스트).

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Uses ``.get('skeptic_log')`` for backward compat with partial state dicts.
- Entry schema: ``SkepticLogEntry`` from ``deconstructor.skeptic.run_log``.
- 부분 state dict 호환을 위해 ``.get`` 사용.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_skeptic_log_section(state: State) -> list[str]:
    """Format skeptic_log entries or placeholder when empty."""
    skeptic_log = state.get("skeptic_log") or []
    lines = [f"--- SKEPTIC LOG ({len(skeptic_log)}) ---"]
    if not skeptic_log:
        lines.append("  (none)")
        return lines

    for entry in skeptic_log:
        lines.append(f"  [{entry.level}] {entry.code}: {entry.message}")
    return lines
