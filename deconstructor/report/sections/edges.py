"""Verified causal edges section — skeptic-approved links.
검증된 인과 엣지 섹션 — 스켉틱 승인 링크.

Purpose / 목적
--------------
Displays ``state['verified_edges']`` with human-readable subjects resolved
from ``completed_facts`` IDs (falls back to truncated UUID).
``state['verified_edges']``를 ``completed_facts`` ID→subject로 해석해 표시
(없으면 UUID 앞 8자).

Pipeline position / 파이프라인 위치
-----------------------------------
After remaining facts; reflects output of verify + skeptic nodes.
remaining facts 이후; verify + skeptic 노드 산출.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``id_to_subject`` only maps completed facts; edges to pending facts show raw id.
- Probability and latency come from ``CausalEdge`` model — keep units (ms) in label.
- completed에 없는 팩트는 raw id 표시.
- ``CausalEdge`` 필드 단위(ms) 라벨 유지.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State


def format_edges_section(state: State) -> list[str]:
    """Render verified edges with subject labels and edge metadata."""
    edges = state["verified_edges"]
    lines = [f"--- VERIFIED CAUSAL EDGES ({len(edges)}) ---"]
    if not edges:
        lines.append("  (none)")
        return lines

    # Resolve UUIDs to subject strings for operator readability.
    # 운영자 가독성을 위해 UUID → subject.
    id_to_subject = {f.id: f.subject for f in state["completed_facts"]}
    for edge in edges:
        src = id_to_subject.get(edge.source_fact_id, edge.source_fact_id[:8])
        tgt = id_to_subject.get(edge.target_fact_id, edge.target_fact_id[:8])
        lines.append(
            f"  {src} -> {tgt}  p={edge.probability}  latency={edge.latency}ms"
        )
    return lines
