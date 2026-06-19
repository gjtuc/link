"""
Step 4 — Critical node Pyvis override (Micro-step S4-*)
=======================================================

is_critical == True 이면 provenance 색상보다 최우선 적용.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COLOR_CRITICAL = "#e63946"
COLOR_CRITICAL_BORDER = "#c1121f"
CRITICAL_NODE_SIZE = 26  # legacy tests / API; viz는 연결 수 기반 크기 우선
DEFAULT_NODE_SIZE = 18
MAX_NODE_SIZE = 42
DEGREE_SIZE_STEP = 4
CRITICAL_FONT_COLOR = "white"


def resolve_node_size_from_degree(*, in_degree: int = 0, out_degree: int = 0) -> int:
    """
    CAUSES 연결 수에 비례해 노드 크기 확대 (색 대신 직관적 hub 표시).

    in/out 합이 0~1이면 기본 크기, 2개부터 단계적으로 커짐 (상한 MAX_NODE_SIZE).
    """
    total = in_degree + out_degree
    if total <= 1:
        return DEFAULT_NODE_SIZE
    return min(MAX_NODE_SIZE, DEFAULT_NODE_SIZE + (total - 1) * DEGREE_SIZE_STEP)


def _log(step: str, msg: str) -> None:
    line = f"[STORM-S4-{step}] {msg}"
    logger.info(line)
    print(line)


@dataclass(frozen=True)
class CriticalNodeVisualStyle:
    """Pyvis critical 노드 강제 스타일."""

    color: str
    border_color: str
    size: int
    shadow: bool
    font_color: str
    font_bold: bool


def resolve_critical_style(*, stress_level: int) -> CriticalNodeVisualStyle:
    """[STORM-S4-2] provenance 무시, 붉은 경보 스타일 반환."""
    _log(
        "2",
        f"override provenance -> color={COLOR_CRITICAL} size={CRITICAL_NODE_SIZE} "
        f"shadow=True stress={stress_level}",
    )
    return CriticalNodeVisualStyle(
        color=COLOR_CRITICAL,
        border_color=COLOR_CRITICAL_BORDER,
        size=CRITICAL_NODE_SIZE,
        shadow=True,
        font_color=CRITICAL_FONT_COLOR,
        font_bold=True,
    )


def format_critical_tooltip_prefix(stress_level: int) -> str:
    """[STORM-S4-3] hover tooltip 첫 줄 — HTML 붉은 경고."""
    _log("3", f"tooltip prefix CRITICAL WARNING stress={stress_level}")
    return (
        f'<span style="color:{COLOR_CRITICAL};font-weight:bold;">'
        f"🚨 [CRITICAL WARNING] Stress Level: {stress_level}</span>"
    )


def log_critical_nodes_fetched(count: int) -> None:
    """[STORM-S4-1] Neo4j fetch에서 critical 노드 매핑 로그."""
    _log("1", f"mapped {count} critical node(s) from Neo4j fetch")


def build_critical_pyvis_kwargs(
    *,
    label: str,
    tooltip: str,
    style: CriticalNodeVisualStyle,
) -> dict:
    """Pyvis add_node kwargs for critical nodes."""
    return {
        "label": label,
        "title": tooltip,
        "size": style.size,
        "shadow": style.shadow,
        "color": {
            "background": style.color,
            "border": style.border_color,
            "highlight": {
                "background": style.color,
                "border": "#ffffff",
            },
        },
        "font": {
            "color": style.font_color,
            "size": 14,
            "face": "Segoe UI",
            "bold": style.font_bold,
        },
    }
