"""
Step 1 — Pyvis provenance 스타일 맵 (Micro-step S1-6)
======================================================

| source_type | check_status | 노드 색     | opacity | 라벨     | 엣지   |
|-------------|--------------|------------|---------|----------|--------|
| extracted   | *            | 파랑       | 1.0     | —        | 실선   |
| inferred    | pending      | 노랑       | 1.0     | —        | 점선   |
| inferred    | dropped      | 노랑       | 0.4     | ✖ prefix | 점선   |
| verified    | promoted     | 초록       | 1.0     | —        | 실선   |
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from deconstructor.provenance.types import is_ghost_dropped

logger = logging.getLogger(__name__)

COLOR_EXTRACTED = "#4cc9f0"
COLOR_INFERRED = "#ffd166"
COLOR_VERIFIED = "#06d6a0"
COLOR_EDGE_CAUSAL = "#f72585"
COLOR_EDGE_HYPOTHESIS = "#ffd166"


@dataclass(frozen=True)
class NodeVisualStyle:
    color: str
    opacity: float
    label_prefix: str
    border_color: str | None = None


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
    target_check_status: str,
    probability: float,
) -> EdgeVisualStyle:
    """
    엔드포인트 provenance 로 CAUSES 선 스타일 결정.

    inferred/dropped 쪽 연결 → 노란 점선 (가설·고스트).
    verified/extracted 인과 → 분홍 실선.
    """
    hypothesis_like = (
        source_type == "inferred"
        or target_type == "inferred"
        or is_ghost_dropped(target_type, target_check_status)
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
            width=1.5 + probability,
            opacity=opacity,
        )

    return EdgeVisualStyle(
        color=COLOR_EDGE_CAUSAL,
        dashes=False,
        width=2 + probability * 2,
        opacity=1.0,
    )
