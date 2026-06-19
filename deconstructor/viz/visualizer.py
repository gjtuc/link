"""
Step 3 — Pyvis 렌더링 엔진 (Provenance Step 1 연동)
===================================================

Provenance 시각화 (S1-6):
  extracted  → 파란 실선
  inferred   → 노란 점선
  dropped    → 노란 점선 + opacity 0.4 + ✖ 라벨
  verified   → 초록 실선
"""

from __future__ import annotations

import logging
from pathlib import Path

from pyvis.network import Network

from deconstructor.provenance.viz_style import resolve_edge_style, resolve_node_style
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

logger = logging.getLogger(__name__)


def _log(step: str, msg: str) -> None:
    line = f"[VIZ-S3-{step}] {msg}"
    logger.info(line)
    print(line)


def _node_tooltip(node: GraphNode) -> str:
    lines = [
        f"subject: {node.subject}",
        f"state_change: {node.state_change}",
        f"timestamp: {node.timestamp or 'n/a'}",
        f"source_type: {node.source_type}",
        f"check_status: {node.check_status}",
    ]
    if node.check_status == "dropped":
        lines.append("status: REJECTED ghost hypothesis")
    return "<br>".join(lines)


def _edge_tooltip(edge: GraphEdge) -> str:
    latency = f"{edge.latency} ms" if edge.latency is not None else "n/a"
    return f"probability: {edge.probability:.3f}<br>latency: {latency}"


def build_pyvis_network(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    title: str = "Deconstructor Causal Graph",
) -> Network:
    """GraphNode provenance → pyvis 색·투명도·점선/실선."""
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

    _log("2", f"adding {len(nodes)} nodes with provenance styling [PROV-S1-6]")
    for node in nodes:
        style = resolve_node_style(node.source_type, node.check_status)
        label = (node.subject or node.id[:8])
        if style.label_prefix:
            label = f"{style.label_prefix}{label}"

        node_kwargs: dict = {
            "label": label,
            "title": _node_tooltip(node),
            "color": style.color,
            "size": 22,
        }
        if style.opacity < 1.0:
            node_kwargs["opacity"] = style.opacity
        if style.border_color:
            node_kwargs["borderWidth"] = 2
            node_kwargs["color"] = {
                "background": style.color,
                "border": style.border_color,
                "highlight": {"background": style.color, "border": "#ef476f"},
            }

        net.add_node(node.id, **node_kwargs)

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
            "label": f"{edge.probability:.2f}",
            "color": estyle.color,
            "arrows": "to",
            "width": estyle.width,
        }
        if estyle.dashes:
            edge_kwargs["dashes"] = True
        if estyle.opacity < 1.0:
            edge_kwargs["color"] = {
                "color": estyle.color,
                "opacity": estyle.opacity,
            }

        net.add_edge(edge.source_id, edge.target_id, **edge_kwargs)

    _log("4", "applying physics + hover interaction options")
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
    "zoomView": true
  },
  "edges": {
    "smooth": { "type": "dynamic" },
    "arrows": { "to": { "enabled": true, "scaleFactor": 1.2 } }
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
    net = build_pyvis_network(nodes, edges, title=title)
    output_path = output_path.resolve()
    _log("5", f"save_graph → {output_path}")
    net.save_graph(str(output_path))
    return output_path
