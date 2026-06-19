"""
Step 3 — Pyvis 렌더링 (provenance 색 + 단순 노드·엣지)
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
from deconstructor.storm.viz_style import DEFAULT_NODE_SIZE
from deconstructor.viz.legend import inject_legend_into_html
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

logger = logging.getLogger(__name__)

NODE_SIZE = DEFAULT_NODE_SIZE
NODE_FONT_SIZE = 16
EDGE_FONT_SIZE = 12
NODE_FONT_COLOR = "#e8e8e8"
GRAPH_BG_COLOR = "#1a1a2e"
GRAPH_LABEL_COLOR = "#e8e8e8"
EDGE_ARROW_SCALE = 0.5
ANCHOR_EDGE_COLOR = COLOR_VERIFIED
ANCHOR_EDGE_WIDTH = 2.0
MAX_LABEL_LEN = 28


def _truncate_label(text: str) -> str:
    text = (text or "").strip()
    if len(text) <= MAX_LABEL_LEN:
        return text
    return text[: MAX_LABEL_LEN - 1] + "…"


def _node_legend_class(node: GraphNode) -> str:
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


def _provenance_summary_ko(node: GraphNode) -> str:
    is_human = getattr(node, "author", None) == "human"
    if is_ghost_dropped(node.source_type, node.check_status):
        return "흐린 노랑 · 기각된 가설"
    if is_promoted_inferred(node.source_type, node.check_status):
        if is_human:
            return "노랑+초록 · 사용자 가설 (Fact-Checker 통과)"
        return "노랑+초록 · Dreamer 가설 (Fact-Checker 통과)"
    if node.source_type == "inferred":
        if is_human:
            return "노랑 · 사용자 가설 (미검증)"
        return "노랑 · Dreamer 가설 (미검증)"
    if node.source_type == "verified":
        return "초록 · 검증된 사실"
    return "파랑 · 원문에서 추출"


def _node_tooltip(node: GraphNode) -> str:
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
    if node.reasoning and node.source_type == "inferred":
        details.append(f"메커니즘: {node.reasoning}")
    if getattr(node, "author", None) == "human":
        details.append("작성: 사용자 (Human-in-the-loop)")
    elif node.source_type == "inferred":
        details.append("작성: Dreamer (LLM)")
    if node.stress_level or node.is_critical:
        details.append(f"stress: {node.stress_level} · critical: {node.is_critical}")
    sections.append("\n".join(details))
    return "\n\n".join(sections)


def _edge_tooltip(edge: GraphEdge) -> str:
    latency = f"{edge.latency} ms" if edge.latency is not None else "없음"
    return f"회색 실선 · 검증된 인과 (CAUSES)\n시차(latency): {latency}"


def _build_node_kwargs(node: GraphNode) -> dict:
    style = resolve_node_style(node.source_type, node.check_status)
    label = _truncate_label(node.subject or node.id[:8])
    if style.label_prefix:
        label = f"{style.label_prefix}{label}"

    node_kwargs: dict = {
        "label": label,
        "title": _node_tooltip(node),
        "shape": "dot",
        "size": NODE_SIZE,
        "font": {
            "size": NODE_FONT_SIZE,
            "color": NODE_FONT_COLOR,
            "face": "Segoe UI",
            "align": "center",
        },
    }
    if style.opacity < 1.0:
        node_kwargs["opacity"] = style.opacity

    border_width = int(style.border_width or 0) if style.border_color else 0
    border_rgba = style.border_color if border_width > 0 else "rgba(0,0,0,0)"
    node_kwargs["borderWidth"] = border_width
    highlight_border = style.border_color or COLOR_VERIFIED
    if is_promoted_inferred(node.source_type, node.check_status):
        highlight_border = COLOR_VERIFIED
    node_kwargs["color"] = {
        "background": style.color,
        "border": border_rgba,
        "highlight": {
            "background": style.color,
            "border": highlight_border if style.border_color else "rgba(232,232,232,0.45)",
        },
    }
    return node_kwargs


def _add_anchor_hint_edges(
    net: Network,
    nodes: list[GraphNode],
    node_by_id: dict[str, GraphNode],
) -> int:
    count = 0
    for node in nodes:
        if node.source_type != "inferred":
            continue
        anchor_id = node.anchor_fact_id
        if not anchor_id or anchor_id not in node_by_id:
            continue
        net.add_edge(
            anchor_id,
            node.id,
            id=f"anchor-{anchor_id}-{node.id}",
            title="Anchor — 가설 노드에 마우스를 올리면 원천 방향 점선 표시",
            hidden=True,
            anchor_hover_only=True,
            dashes=True,
            width=ANCHOR_EDGE_WIDTH,
            color={"color": ANCHOR_EDGE_COLOR, "opacity": 0.9},
            arrows={"to": {"enabled": True, "scaleFactor": 0.45}},
            legend_class="anchor-dashed",
        )
        count += 1
    if count:
        _log("3b", f"added {count} hidden anchor hint edge(s)")
    return count


def build_pyvis_network(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    title: str = "Deconstructor Causal Graph",
) -> Network:
    """GraphNode → pyvis Network (고정 크기 원형 노드 + 단순 physics)."""
    _log("1", f"init Network directed=True title={title!r}")
    net = Network(
        height="100%",
        width="100%",
        bgcolor=GRAPH_BG_COLOR,
        font_color=GRAPH_LABEL_COLOR,
        directed=True,
        heading="",
    )

    node_by_id = {n.id: n for n in nodes}
    _log("2", f"adding {len(nodes)} nodes (size={NODE_SIZE})")
    for node in nodes:
        node_kwargs = _build_node_kwargs(node)
        node_kwargs["legend_class"] = _node_legend_class(node)
        if node.anchor_fact_id:
            node_kwargs["anchor_fact_id"] = node.anchor_fact_id
        net.add_node(node.id, **node_kwargs)

    _log("3", f"adding {len(edges)} edges")
    for edge in edges:
        src = node_by_id.get(edge.source_id)
        tgt = node_by_id.get(edge.target_id)
        estyle = resolve_edge_style(
            source_type=src.source_type if src else "extracted",
            target_type=tgt.source_type if tgt else "extracted",
            source_check_status=src.check_status if src else "active",
            target_check_status=tgt.check_status if tgt else "active",
            probability=edge.probability,
        )
        edge_kwargs: dict = {
            "title": _edge_tooltip(edge),
            "color": estyle.color,
            "arrows": {"to": {"enabled": True, "scaleFactor": EDGE_ARROW_SCALE}},
            "width": estyle.width,
            "font": {"size": EDGE_FONT_SIZE, "color": "#8a9199", "face": "Segoe UI"},
            "smooth": False,
        }
        if abs(edge.probability - 1.0) > 1e-6:
            edge_kwargs["label"] = f"{edge.probability:.2f}"
        if estyle.dashes:
            edge_kwargs["dashes"] = True
        if estyle.opacity < 1.0:
            edge_kwargs["color"] = {"color": estyle.color, "opacity": estyle.opacity}
        edge_kwargs["legend_class"] = _edge_legend_class(dashes=estyle.dashes)
        net.add_edge(edge.source_id, edge.target_id, **edge_kwargs)

    _add_anchor_hint_edges(net, nodes, node_by_id)

    _log("4", "applying simple physics options")
    net.set_options(
        f"""
{{
  "physics": {{
    "enabled": true,
    "stabilization": {{ "iterations": 100 }},
    "barnesHut": {{
      "gravitationalConstant": -8000,
      "centralGravity": 0.3,
      "springLength": 120,
      "springConstant": 0.04,
      "damping": 0.09
    }}
  }},
  "interaction": {{
    "hover": true,
    "tooltipDelay": 120,
    "dragNodes": true,
    "dragView": true,
    "zoomView": true
  }},
  "edges": {{
    "smooth": false,
    "arrows": {{ "to": {{ "enabled": true, "scaleFactor": {EDGE_ARROW_SCALE} }} }},
    "color": {{ "color": "#b8c1cc", "highlight": "#8a9199" }},
    "width": 1
  }},
  "nodes": {{
    "shape": "dot",
    "font": {{ "size": {NODE_FONT_SIZE}, "color": "#e8e8e8", "face": "Segoe UI" }},
    "scaling": {{ "min": {NODE_SIZE}, "max": {NODE_SIZE} }}
  }}
}}
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
    net = build_pyvis_network(nodes, edges, title=title)
    output_path = output_path.resolve()
    _log("5", f"save_graph → {output_path}")
    net.save_graph(str(output_path))
    inject_legend_into_html(output_path)
    return output_path
