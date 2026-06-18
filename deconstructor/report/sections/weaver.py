"""Weaver section — graph persistence outcome summary.
위버 섹션 — 그래프 영속화 결과 요약.

Purpose / 목적
--------------
Reports ``state.get('weaver_result')`` — mode (e.g. console vs DB), counts
of nodes/edges written, skip reason, and sample edge pairs.
``state.get('weaver_result')`` — mode, nodes/edges 기록 수, skip 사유, 샘플 엣지 쌍.

Pipeline position / 파이프라인 위치
-----------------------------------
Near end of report, after partial-run block; reflects final weaver node.
리포트 후반, partial 블록 다음; 최종 weaver 노드 반영.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Shows at most 5 ``edge_pairs`` — increase only if operators need more samples.
- ``(not run)`` when ``weaver_result`` is None (early abort or dry config).
- ``edge_pairs`` 최대 5개 — 필요 시만 확대.
- ``weaver_result is None`` → ``(not run)``.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_weaver_section(state: State) -> list[str]:
    """Format WeaverResult summary for console report."""
    weaver = state.get("weaver_result")
    lines = ["--- WEAVER ---"]
    if weaver is None:
        lines.append("  (not run)")
        return lines

    lines.append(f"  mode            : {weaver.mode}")
    lines.append(f"  nodes_written   : {weaver.nodes_written}")
    lines.append(f"  edges_written   : {weaver.edges_written}")
    if weaver.skipped_reason:
        lines.append(f"  skipped         : {weaver.skipped_reason}")
    # Sample first five edge pairs — full list may be large.
    # 처음 5개 엣지 쌍만 샘플.
    for pair in weaver.edge_pairs[:5]:
        lines.append(f"  edge            : {pair[0][:8]}.. -> {pair[1][:8]}..")
    return lines
