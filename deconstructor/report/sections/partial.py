"""Partial run section — depth cap exhaustion banner.
부분 실행 섹션 — 깊이 상한 소진 배너.

Purpose / 목적
--------------
When ``state['partial_run']`` is true, shows machine reason code and flag.
Written by graph nodes using ``detect_partial_run`` semantics.
``state['partial_run']``이 True일 때 기계 readable reason 표시.
``detect_partial_run`` 의미와 맞춰 그래프 노드가 설정.

Pipeline position / 파이프라인 위치
-----------------------------------
Inserted in ``compose`` only when ``format_partial_run_section`` returns
non-empty list (skipped entirely on successful null-floor runs).
성공(null floor) 실행에서는 **섹션 전체 생략**; partial일 때만 compose 삽입.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Return ``[]`` when not partial — compose checks truthiness of return value.
- Reason codes defined in ``pipeline.partial_run`` (e.g. ``REASON_DEPTH_CAP``).
- partial 아님 → ``[]`` 반환.
- reason 코드는 ``pipeline.partial_run`` 참고.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_partial_run_section(state: State) -> list[str]:
    """Return partial-run lines or empty list to omit section."""
    if not state.get("partial_run"):
        return []

    return [
        "--- PARTIAL RUN ---",
        "  partial_run     : True",
        f"  reason          : {state.get('partial_run_reason', '')}",
    ]
