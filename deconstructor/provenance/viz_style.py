"""
Step 1 — Pyvis provenance 스타일 맵 (Micro-step S1-6)
======================================================

| source_type | check_status | 노드 색     | opacity | 라벨     | 엣지   |
|-------------|--------------|------------|---------|----------|--------|
| extracted   | *            | 파랑       | 1.0     | —        | 실선   |
| inferred    | pending      | 노랑       | 1.0     | —        | 점선   |
| inferred    | promoted     | 노랑       | 1.0     | —        | 실선   |  ← FC 통과: 초록 테두리
| inferred    | dropped      | 노랑       | 0.4     | ✖ prefix | 점선   |
| verified    | *            | 초록       | 1.0     | —        | 실선   |
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from deconstructor.provenance.types import is_ghost_dropped, is_promoted_inferred

logger = logging.getLogger(__name__)

# Bloom/Neo4j 스타일 — 중간 채도, 연한 노드·회색 화살표
COLOR_EXTRACTED = "#8ecae6"
COLOR_INFERRED = "#f4a261"
COLOR_VERIFIED = "#90be6d"
COLOR_EDGE_CAUSAL = "#b8c1cc"
COLOR_EDGE_HYPOTHESIS = "#cdd3db"


@dataclass(frozen=True)
class NodeVisualStyle:
    color: str
    opacity: float
    label_prefix: str
    border_color: str | None = None
    border_width: int = 2


@dataclass(frozen=True)
class EdgeVisualStyle:
    color: str
    dashes: bool
    width: float
    opacity: float = 1.0


def _log(msg: str) -> None:
    line = f"[PROV-S1-6] {msg}"
    logger.info(line)
    print(line)


def resolve_node_style(source_type: str, check_status: str) -> NodeVisualStyle:
    """GraphNode.source_type + check_status → pyvis 노드 스타일."""
    if is_ghost_dropped(source_type, check_status):
        _log(f"style ghost dropped node source_type={source_type}")
        return NodeVisualStyle(
            color=COLOR_INFERRED,
            opacity=0.4,
            label_prefix="✖ ",
            border_color="#ef476f",
        )

    if source_type == "verified":
        _log(f"style verified node check_status={check_status}")
        return NodeVisualStyle(
            color=COLOR_VERIFIED,
            opacity=1.0,
            label_prefix="",
        )

    if is_promoted_inferred(source_type, check_status):
        _log("style inferred/promoted node (Dreamer FC pass — yellow + green border)")
        return NodeVisualStyle(
            color=COLOR_INFERRED,
            opacity=1.0,
            label_prefix="",
            border_color=COLOR_VERIFIED,
            border_width=3,
        )

    if source_type == "inferred":
        _log(f"style inferred node check_status={check_status}")
        return NodeVisualStyle(
            color=COLOR_INFERRED,
            opacity=1.0,
            label_prefix="",
            border_color=COLOR_INFERRED,
        )

    # extracted (default)
    return NodeVisualStyle(
        color=COLOR_EXTRACTED,
        opacity=1.0,
        label_prefix="",
    )


def resolve_edge_style(
    *,
    source_type: str,
    target_type: str,
    source_check_status: str = "active",
    target_check_status: str,
    probability: float,
) -> EdgeVisualStyle:
    """
    엔드포인트 provenance 로 CAUSES 선 스타일 결정.

    inferred/pending·dropped 쪽 연결 → 노란 점선 (가설·고스트).
    inferred/promoted·verified·extracted 인과 → 분홍 실선.
    """

    def _hypothesis_endpoint(source_type: str, check_status: str) -> bool:
        if is_ghost_dropped(source_type, check_status):
            return True
        if source_type == "inferred" and check_status == "pending":
            return True
        return False

    hypothesis_like = _hypothesis_endpoint(source_type, source_check_status) or _hypothesis_endpoint(
        target_type, target_check_status
    )

    if hypothesis_like:
        _log(
            f"edge dashed hypothesis-like "
            f"{source_type}->{target_type} status={target_check_status}"
        )
        opacity = 0.4 if is_ghost_dropped(target_type, target_check_status) else 0.85
        return EdgeVisualStyle(
            color=COLOR_EDGE_HYPOTHESIS,
            dashes=True,
            width=0.9 + probability * 0.25,
            opacity=opacity,
        )

    return EdgeVisualStyle(
        color=COLOR_EDGE_CAUSAL,
        dashes=False,
        width=1.0 + probability * 0.35,
        opacity=0.92,
    )
