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
  - extracted=파랑, verified=초록, inferred=노랑, dropped=흐린 노랑+✖
  - ``is_critical=True`` → provenance 무시, 빨강·35px·그림자 (storm/viz_style)
  - **빨간 테두리** (본문색 유지): CRITICAL 노드로 *직접* CAUSES 되는 비-critical 원인
    (예: 파랑 Trump → 빨강 US and Iran 이면 Trump는 파랑+빨간 테두리)

엣지:
  - 검증 CAUSES=분홍 실선, 가설=inferred/dropped 쪽=노랑 점선
  - ``probability`` 라벨: Skeptic 수용 시 항상 1.0 이라 **기본 숫자 라벨 생략**
    (scoring.py: 수용 = decisive 규칙 전원 PASS → passes/len(decisive)=1.0)
  - hover 툴팁에는 ``latency``(원인→결과 ms) 만 표시

Interaction (legend.py 가 HTML에 주입)
--------------------------------------
  - 노드 클릭/dragStart → physics off (움직이는 노드 클릭 어려움 해소)
  - dragEnd → 노드 fixed pin
  - 빈 배경 doubleClick → physics 재개

When to modify / 수정 시점
--------------------------
- CRITICAL 원인 강조: ``_critical_cause_ids`` / ``critical_cause`` 플래그
- 확률 gradation 도입 시: ``edge_kwargs["label"]`` 조건 (``abs(p-1.0) > 1e-6``) 조정
- pyvis 템플릿 변경 시: legend.inject_graph_interaction 의 replace 문자열 동기화

Key files / 관련 파일
---------------------
  provenance/viz_style.py  — 노드·엣지 provenance 색
  storm/viz_style.py       — CRITICAL override, COLOR_CRITICAL
  viz/legend.py            — 범례 HTML + vis.js physics freeze 스크립트
  viz/neo4j_utils.py       — Step 2 fetch (CAUSES only, rejected 미포함)
"""

from __future__ import annotations

import logging
from pathlib import Path

from pyvis.network import Network

from deconstructor.provenance.viz_style import resolve_edge_style, resolve_node_style
from deconstructor.storm.viz_style import (
    COLOR_CRITICAL,
    build_critical_pyvis_kwargs,
    format_critical_tooltip_prefix,
    resolve_critical_style,
)
from deconstructor.viz.legend import inject_legend_into_html
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

logger = logging.getLogger(__name__)

# 일반 노드 pyvis size (storm CRITICAL_NODE_SIZE=35 와 대비)
DEFAULT_NODE_SIZE = 22

# CRITICAL 로 직접 인과되는 upstream 노드 테두리 — fill 은 provenance 유지
CRITICAL_CAUSE_BORDER_WIDTH = 3


def _critical_cause_ids(critical_ids: set[str], edges: list[GraphEdge]) -> set[str]:
    """
    CRITICAL(빨강) 노드로 *1-hop* CAUSES 되는 비-critical 원인 노드 id 집합.

    설계 의도:
      사용자가 "빨강이 어디서 왔는지" 한눈에 보게 하려고, 결과(CRITICAL) 노드의
      직접 부모만 빨간 테두리로 표시한다. 다-hop 전파(조부모까지)는 하지 않음 —
      화살표 방향으로 추적하면 충분하다고 판단.

    Args:
        critical_ids: ``GraphNode.is_critical`` 인 id
        edges: Neo4j CAUSES (Skeptic verified only)

    Returns:
        테두리를 COLOR_CRITICAL 로 칠할 source node id (critical 자신은 제외)
    """
    return {
        edge.source_id
        for edge in edges
        if edge.target_id in critical_ids and edge.source_id not in critical_ids
    }


def _log(step: str, msg: str) -> None:
    line = f"[VIZ-S3-{step}] {msg}"
    logger.info(line)
    print(line)


def _log_storm_s4(step: str, msg: str) -> None:
    line = f"[STORM-S4-{step}] {msg}"
    logger.info(line)
    print(line)


def _node_tooltip(node: GraphNode) -> str:
    """pyvis ``title`` (hover HTML). CRITICAL 이면 경고 prefix 선행."""
    lines: list[str] = []
    if node.is_critical:
        lines.append(format_critical_tooltip_prefix(node.stress_level))
    lines.extend(
        [
            f"subject: {node.subject}",
            f"state_change: {node.state_change}",
            f"timestamp: {node.timestamp or 'n/a'}",
            f"source_type: {node.source_type}",
            f"check_status: {node.check_status}",
            f"stress_level: {node.stress_level}",
            f"is_critical: {node.is_critical}",
        ]
    )
    if node.check_status == "dropped":
        lines.append("status: REJECTED ghost hypothesis")
    return "<br>".join(lines)


def _edge_tooltip(edge: GraphEdge) -> str:
    """
    엣지 hover. probability 는 수용 엣지에서 항상 1.0 이라 생략 (UI 노이즈 방지).

    latency: skeptic scoring.compute_latency_ms — 양쪽 timestamp 있을 때만 ms.
    """
    latency = f"{edge.latency} ms" if edge.latency is not None else "n/a"
    return f"latency: {latency}"


def _build_provenance_node_kwargs(
    node: GraphNode,
    label: str,
    *,
    critical_cause: bool = False,
) -> dict:
    """
    비-critical 노드용 pyvis kwargs.

    ``critical_cause=True`` 이면 background 는 provenance 색 유지, border 만
    ``COLOR_CRITICAL`` (#ff0033) + ``CRITICAL_CAUSE_BORDER_WIDTH``.

    dropped ghost 는 provenance 가 이미 border (#ef476f) 를 줄 수 있음;
    critical_cause 가 True 이면 storm 빨강 테두리가 우선 (CRITICAL 유입 경로 강조).
    """
    style = resolve_node_style(node.source_type, node.check_status)
    node_kwargs: dict = {
        "label": label,
        "title": _node_tooltip(node),
        "color": style.color,
        "size": DEFAULT_NODE_SIZE,
    }
    if style.opacity < 1.0:
        node_kwargs["opacity"] = style.opacity

    border = style.border_color
    border_width = 2
    if critical_cause:
        border = COLOR_CRITICAL
        border_width = CRITICAL_CAUSE_BORDER_WIDTH

    if border:
        node_kwargs["borderWidth"] = border_width
        node_kwargs["color"] = {
            "background": style.color,
            "border": border,
            "highlight": {
                "background": style.color,
                "border": "#ffffff" if critical_cause else "#ef476f",
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
      1. is_critical → storm 전체 override (빨강·큼)
      2. critical_cause upstream → provenance + 빨간 테두리
      3. 그 외 → provenance 색만
    """
    _log("1", f"init Network directed=True title={title!r}")
    net = Network(
        height="800px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#e8e8e8",
        directed=True,
        heading=title,
    )

    node_by_id = {n.id: n for n in nodes}
    critical_ids = {n.id for n in nodes if n.is_critical}
    critical_cause_ids = _critical_cause_ids(critical_ids, edges)
    if critical_cause_ids:
        _log_storm_s4(
            "5",
            f"critical-cause red border on {len(critical_cause_ids)} upstream node(s)",
        )

    _log("2", f"adding {len(nodes)} nodes (provenance + storm critical override)")
    for node in nodes:
        style = resolve_node_style(node.source_type, node.check_status)
        label = node.subject or node.id[:8]
        if style.label_prefix:
            label = f"{style.label_prefix}{label}"

        if node.is_critical:
            _log_storm_s4(
                "4",
                f"apply critical override node={node.subject!r} "
                f"provenance={node.source_type} ignored",
            )
            critical_style = resolve_critical_style(stress_level=node.stress_level)
            node_kwargs = build_critical_pyvis_kwargs(
                label=label,
                tooltip=_node_tooltip(node),
                style=critical_style,
            )
        else:
            node_kwargs = _build_provenance_node_kwargs(
                node,
                label,
                critical_cause=node.id in critical_cause_ids,
            )

        net.add_node(node.id, **node_kwargs)

    # critical 노드 font/shadow — build_critical_pyvis_kwargs 일부와 중복 보강
    for node_dict in net.nodes:
        if node_dict.get("id") in critical_ids:
            node_dict["font"] = {
                "color": "white",
                "size": 16,
                "face": "arial",
                "bold": True,
            }
            node_dict["shadow"] = True

    _log("3", f"adding {len(edges)} edges with dashed/solid by provenance")
    for edge in edges:
        src = node_by_id.get(edge.source_id)
        tgt = node_by_id.get(edge.target_id)
        src_type = src.source_type if src else "extracted"
        tgt_type = tgt.source_type if tgt else "extracted"
        tgt_status = tgt.check_status if tgt else "active"

        estyle = resolve_edge_style(
            source_type=src_type,
            target_type=tgt_type,
            target_check_status=tgt_status,
            probability=edge.probability,
        )

        edge_kwargs: dict = {
            "title": _edge_tooltip(edge),
            "color": estyle.color,
            "arrows": "to",
            "width": estyle.width,
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

        net.add_edge(edge.source_id, edge.target_id, **edge_kwargs)

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
    "smooth": { "type": "dynamic" },
    "arrows": { "to": { "enabled": true, "scaleFactor": 1.2 } }
  },
  "nodes": {
    "shadow": {
      "enabled": true,
      "color": "rgba(255,0,51,0.45)",
      "size": 25,
      "x": 2,
      "y": 2
    }
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
