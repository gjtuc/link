"""
Step 3 — Pyvis 렌더링 엔진 (Provenance + Storm Step 4 critical override)
========================================================================

Purpose / 목적
--------------
Neo4j ``GraphNode`` / ``GraphEdge`` 를 pyvis ``Network`` 로 변환하고
``graph_output.html`` 을 생성한다. 노드 색·크기는 provenance + Perfect Storm
정책을 따르며, HTML 저장 후 ``legend.inject_legend_into_html`` 로
범례·클릭 인터랙션을 후처리 주입한다.

Pipeline position / 파이프라인 위치
---------------------------------
  neo4j_utils.fetch_causal_graph  →  **build_pyvis_network / render_to_html**
  →  legend.inject_legend_into_html  →  graph_output.html (브라우저)

Visual encoding (2026-06 UI 세션에서 확정)
------------------------------------------
노드:
  - extracted=파랑, verified=초록, inferred pending=노랑, inferred promoted=노랑+초록 테두리, dropped=흐린 노랑+✖
  - 크기 = CAUSES in+out 연결 수 (hub일수록 큼, storm ``resolve_node_size_from_degree``)
  - ``anchor_fact_id`` on node → hover 시 **초록 점선** (Skeptic CAUSES 와 별도, ``anchor_hover_only``)

엣지:
  - 검증 CAUSES=연회색 실선 (Skeptic 통과)
  - 가설 쪽=연한 회색 점선
  - Dreamer anchor=**hidden** 초록 점선, ``hoverNode`` 시에만 표시 (legend.py JS)

툴팁:
  - plain text + ``\\n``, 한국어 **요약 / 자세히** (HTML ``<br>`` 사용 안 함)

Interaction (legend.py 가 HTML에 주입)
--------------------------------------
  - 노드 클릭/dragStart → physics off (움직이는 노드 클릭 어려움 해소)
  - dragEnd → 노드 fixed pin
  - 빈 배경 doubleClick → physics 재개

When to modify / 수정 시점
--------------------------
- hub 크기: ``storm/viz_style.resolve_node_size_from_degree`` · ``_degree_maps``
- 확률 gradation 도입 시: ``edge_kwargs["label"]`` 조건 (``abs(p-1.0) > 1e-6``) 조정
- pyvis 템플릿 변경 시: legend.inject_graph_interaction 의 replace 문자열 동기화

Key files / 관련 파일
---------------------
  provenance/viz_style.py  — 노드·엣지 provenance 색
  storm/viz_style.py       — 연결 수 기반 노드 크기
  viz/legend.py            — 범례 HTML + vis.js physics freeze 스크립트
  viz/neo4j_utils.py       — Step 2 fetch (CAUSES only, rejected 미포함)
"""

from __future__ import annotations

import logging
from pathlib import Path

from pyvis.network import Network

from deconstructor.provenance.types import is_ghost_dropped, is_promoted_inferred
from deconstructor.provenance.viz_style import (
    COLOR_VERIFIED,
    resolve_edge_style,
    resolve_node_style,
)
from deconstructor.storm.viz_style import (
    DEFAULT_NODE_SIZE as STORM_DEFAULT_NODE_SIZE,
    resolve_node_size_from_degree,
)
from deconstructor.viz.legend import inject_legend_into_html
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

logger = logging.getLogger(__name__)

# 일반 노드 — Bloom 유사 비율; hub는 연결 수로 크기만 확대
DEFAULT_NODE_SIZE = STORM_DEFAULT_NODE_SIZE
NODE_FONT_SIZE = 13
NODE_FONT_COLOR = "#3a3d42"
GRAPH_BG_COLOR = "#1a1a2e"
GRAPH_LABEL_COLOR = "#e8e8e8"
EDGE_ARROW_SCALE = 0.55
ANCHOR_EDGE_COLOR = COLOR_VERIFIED
ANCHOR_EDGE_WIDTH = 2.0


def _degree_maps(edges: list[GraphEdge]) -> tuple[dict[str, int], dict[str, int]]:
    """노드별 CAUSES in-degree / out-degree."""
    in_degree: dict[str, int] = {}
    out_degree: dict[str, int] = {}
    for edge in edges:
        out_degree[edge.source_id] = out_degree.get(edge.source_id, 0) + 1
        in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1
    return in_degree, out_degree


def _node_font_size_for(node_size: int) -> int:
    bump = max(0, (node_size - DEFAULT_NODE_SIZE) // 4)
    return min(15, NODE_FONT_SIZE + bump)


def _node_legend_class(node: GraphNode) -> str:
    """범례 hover 필터용 provenance 분류."""
    if is_ghost_dropped(node.source_type, node.check_status):
        return "dropped"
    if node.source_type == "verified":
        return "verified"
    if is_promoted_inferred(node.source_type, node.check_status):
        return "promoted"
    if node.source_type == "inferred":
        return "inferred"
    return "extracted"


def _edge_legend_class(*, dashes: bool) -> str:
    return "edge-dashed" if dashes else "edge-solid"


def _log(step: str, msg: str) -> None:
    line = f"[VIZ-S3-{step}] {msg}"
    logger.info(line)
    print(line)


def _log_storm_s4(step: str, msg: str) -> None:
    line = f"[STORM-S4-{step}] {msg}"
    logger.info(line)
    print(line)


def _provenance_summary_ko(node: GraphNode) -> str:
    """범례와 맞는 한 줄 provenance 설명."""
    if is_ghost_dropped(node.source_type, node.check_status):
        return "흐린 노랑 · 기각된 가설"
    if is_promoted_inferred(node.source_type, node.check_status):
        return "노랑+초록 · Dreamer 가설 (Fact-Checker 통과)"
    if node.source_type == "inferred":
        return "노랑 · Dreamer 가설 (미검증)"
    if node.source_type == "verified":
        return "초록 · 검증된 사실"
    return "파랑 · 원문에서 추출"


def _add_anchor_hint_edges(
    net: Network,
    nodes: list[GraphNode],
    node_by_id: dict[str, GraphNode],
) -> int:
    """
    Dreamer anchor: 원천 → inferred 점선 (기본 hidden, hover 시 JS가 표시).

    Skeptic CAUSES 와 별도 — Fact-Checker·Dreamer 출처만 표시.
    """
    count = 0
    for node in nodes:
        if node.source_type != "inferred":
            continue
        anchor_id = node.anchor_fact_id
        if not anchor_id or anchor_id not in node_by_id:
            continue
        edge_id = f"anchor-{anchor_id}-{node.id}"
        net.add_edge(
            anchor_id,
            node.id,
            id=edge_id,
            title="Dreamer anchor — 가설 노드에 마우스를 올리면 표시",
            hidden=True,
            anchor_hover_only=True,
            dashes=True,
            width=ANCHOR_EDGE_WIDTH,
            color={"color": ANCHOR_EDGE_COLOR, "opacity": 0.9},
            arrows={"to": {"enabled": True, "scaleFactor": 0.45}},
            legend_class="anchor-dashed",
            smooth={"type": "continuous"},
        )
        count += 1
    if count:
        _log("3b", f"added {count} hidden anchor hint edge(s) (show on inferred hover)")
    return count


def _node_tooltip(
    node: GraphNode,
    *,
    in_degree: int = 0,
    out_degree: int = 0,
    node_by_id: dict[str, GraphNode] | None = None,
) -> str:
    """pyvis ``title`` — plain text + ``\\n`` (vis-tooltip ``pre-line``)."""
    sections: list[str] = []

    summary = [
        f"요약: {_provenance_summary_ko(node)}",
        node.subject,
        node.state_change,
    ]
    if node.source_type == "inferred" and node.anchor_fact_id:
        summary.append("※ 마우스를 올리면 원천(파랑) 방향 점선 화살표")
    sections.append("\n".join(summary))

    details: list[str] = ["자세히"]
    if node.timestamp:
        details.append(f"시각: {node.timestamp}")
    total_conn = in_degree + out_degree
    if total_conn:
        details.append(
            f"연결: 들어옴 {in_degree} · 나감 {out_degree} "
            f"(많을수록 노드 큼)"
        )
    if node.reasoning and node.source_type == "inferred":
        details.append(f"메커니즘: {node.reasoning}")
    if node.stress_level or node.is_critical:
        details.append(f"stress: {node.stress_level} · critical: {node.is_critical}")

    sections.append("\n".join(details))
    return "\n\n".join(sections)


def _edge_tooltip(edge: GraphEdge) -> str:
    """엣지 hover — 검증 CAUSES + 시차."""
    latency = f"{edge.latency} ms" if edge.latency is not None else "없음"
    return f"회색 실선 · 검증된 인과 (CAUSES)\n시차(latency): {latency}"


def _build_provenance_node_kwargs(
    node: GraphNode,
    label: str,
    *,
    size: int,
) -> dict:
    """비-critical 노드용 pyvis kwargs (provenance 색 + 연결 수 기반 크기)."""
    style = resolve_node_style(node.source_type, node.check_status)
    font_size = _node_font_size_for(size)
    node_kwargs: dict = {
        "label": label,
        "title": _node_tooltip(node),
        "color": style.color,
        "size": size,
        "font": {
            "size": font_size,
            "color": NODE_FONT_COLOR,
            "face": "Segoe UI",
        },
    }
    if style.opacity < 1.0:
        node_kwargs["opacity"] = style.opacity

    border = style.border_color
    border_width = style.border_width

    if border:
        node_kwargs["borderWidth"] = border_width
        highlight_border = border
        if is_promoted_inferred(node.source_type, node.check_status):
            highlight_border = COLOR_VERIFIED
        node_kwargs["color"] = {
            "background": style.color,
            "border": border,
            "highlight": {
                "background": style.color,
                "border": highlight_border,
            },
        }
    return node_kwargs


def build_pyvis_network(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    title: str = "Deconstructor Causal Graph",
) -> Network:
    """
    GraphNode → pyvis Network (단위 테스트·CLI·웹 UI 공통).

    렌더 우선순위 (노드):
      1. provenance 색 (extracted / inferred / promoted …)
      2. 크기 = CAUSES in+out 연결 수 (hub일수록 큼)
    """
    _log("1", f"init Network directed=True title={title!r}")
    net = Network(
        height="800px",
        width="100%",
        bgcolor=GRAPH_BG_COLOR,
        font_color=GRAPH_LABEL_COLOR,
        directed=True,
        heading="",
    )

    in_degree, out_degree = _degree_maps(edges)
    node_by_id = {n.id: n for n in nodes}

    _log("2", f"adding {len(nodes)} nodes (provenance + degree-based size)")
    for node in nodes:
        style = resolve_node_style(node.source_type, node.check_status)
        label = node.subject or node.id[:8]
        if style.label_prefix:
            label = f"{style.label_prefix}{label}"

        deg_in = in_degree.get(node.id, 0)
        deg_out = out_degree.get(node.id, 0)
        size = resolve_node_size_from_degree(in_degree=deg_in, out_degree=deg_out)
        node_kwargs = _build_provenance_node_kwargs(
            node,
            label,
            size=size,
        )
        node_kwargs["title"] = _node_tooltip(
            node,
            in_degree=deg_in,
            out_degree=deg_out,
            node_by_id=node_by_id,
        )
        node_kwargs["legend_class"] = _node_legend_class(node)
        node_kwargs["legend_hub"] = size > DEFAULT_NODE_SIZE
        if node.anchor_fact_id:
            node_kwargs["anchor_fact_id"] = node.anchor_fact_id
        net.add_node(node.id, **node_kwargs)

    _log("3", f"adding {len(edges)} edges with dashed/solid by provenance")
    for edge in edges:
        src = node_by_id.get(edge.source_id)
        tgt = node_by_id.get(edge.target_id)
        src_type = src.source_type if src else "extracted"
        tgt_type = tgt.source_type if tgt else "extracted"
        src_status = src.check_status if src else "active"
        tgt_status = tgt.check_status if tgt else "active"

        estyle = resolve_edge_style(
            source_type=src_type,
            target_type=tgt_type,
            source_check_status=src_status,
            target_check_status=tgt_status,
            probability=edge.probability,
        )

        edge_kwargs: dict = {
            "title": _edge_tooltip(edge),
            "color": estyle.color,
            "arrows": {"to": {"enabled": True, "scaleFactor": EDGE_ARROW_SCALE}},
            "width": estyle.width,
            "font": {"size": 11, "color": "#8a9199", "face": "Segoe UI", "align": "middle"},
        }
        # Skeptic 수용 = 전 규칙 PASS → probability 항상 1.0; 라벨은 의미 없음.
        # scoring/집계 정책 변경으로 p<1 수용이 가능해지면 자동으로 라벨 표시됨.
        if abs(edge.probability - 1.0) > 1e-6:
            edge_kwargs["label"] = f"{edge.probability:.2f}"
        if estyle.dashes:
            edge_kwargs["dashes"] = True
        if estyle.opacity < 1.0:
            edge_kwargs["color"] = {
                "color": estyle.color,
                "opacity": estyle.opacity,
            }

        edge_kwargs["legend_class"] = _edge_legend_class(dashes=estyle.dashes)
        net.add_edge(edge.source_id, edge.target_id, **edge_kwargs)

    _add_anchor_hint_edges(net, nodes, node_by_id)

    _log("4", "applying physics + hover interaction options")
    # physics/interaction 은 pyvis JSON; 클릭 freeze 는 legend.py 가 HTML 후처리
    net.set_options(
        """
{
  "physics": {
    "enabled": true,
    "stabilization": { "iterations": 150 },
    "barnesHut": {
      "gravitationalConstant": -12000,
      "centralGravity": 0.35,
      "springLength": 220,
      "springConstant": 0.05,
      "damping": 0.12,
      "avoidOverlap": 0.2
    }
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 100,
    "dragNodes": true,
    "dragView": true,
    "zoomView": true,
    "multiselect": false,
    "selectConnectedEdges": false
  },
  "edges": {
    "smooth": { "type": "continuous" },
    "arrows": { "to": { "enabled": true, "scaleFactor": 0.55 } },
    "color": { "color": "#b8c1cc", "highlight": "#8a9199" },
    "width": 1,
    "font": { "size": 11, "color": "#8a9199", "face": "Segoe UI" }
  },
  "nodes": {
    "font": { "size": 13, "color": "#3a3d42", "face": "Segoe UI" },
    "shadow": false
  }
}
"""
    )

    return net


def render_to_html(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    output_path: Path,
    *,
    title: str = "Deconstructor Causal Graph",
) -> Path:
    """
    pyvis 저장 + 범례·인터랙션 주입까지 한 번에.

    ``output_path`` 는 보통 프로젝트 루트 ``graph_output.html`` (.gitignore).
    웹 UI(server.py)는 분석 배치 후 동일 경로를 iframe/새 탭으로 연다.
    """
    net = build_pyvis_network(nodes, edges, title=title)
    output_path = output_path.resolve()
    _log("5", f"save_graph → {output_path}")
    net.save_graph(str(output_path))
    inject_legend_into_html(output_path)
    return output_path
