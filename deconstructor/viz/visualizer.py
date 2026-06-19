"""
Step 3 — Pyvis 렌더링 엔진 (Micro-step)
=======================================

목적:
  neo4j_utils.GraphNode/GraphEdge → pyvis.Network → graph_output.html

시각화 정책 (Step 3 요구):
  1. Physics ON — Barnes-Hut + damping (드래그 시 쫀득한 움직임)
  2. 노드 hover — state_change, timestamp 툴팁 (+ subject 보조)
  3. 엣지 — directed 화살표 명확; 입력은 CAUSES(검증된 인과)만

Micro-steps ([VIZ-S3-...] 로그):
  S3-1  Network 초기화
  S3-2  노드 추가
  S3-3  검증된 엣지만 추가 (rejected 미포함 — 입력 단계에서 이미 보장)
  S3-4  physics / interaction 옵션 주입
  S3-5  HTML 저장

수정 시:
  vis.js JSON 옵션은 pyvis 버전과 호환 확인.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pyvis.network import Network

from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

logger = logging.getLogger(__name__)


def _log(step: str, msg: str) -> None:
    line = f"[VIZ-S3-{step}] {msg}"
    logger.info(line)
    print(line)


def _node_tooltip(node: GraphNode) -> str:
    """Step 3-2: hover 시 state_change, timestamp 필수 노출."""
    return "<br>".join(
        [
            f"subject: {node.subject}",
            f"state_change: {node.state_change}",
            f"timestamp: {node.timestamp or 'n/a'}",
        ]
    )


def _edge_tooltip(edge: GraphEdge) -> str:
    latency = f"{edge.latency} ms" if edge.latency is not None else "n/a"
    return f"probability: {edge.probability:.3f}<br>latency: {latency}"


def build_pyvis_network(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    title: str = "Deconstructor Causal Graph",
) -> Network:
    """
    pyvis Network 객체 생성 (저장 전).

    Rejected correlation 은 Neo4j에 없으므로 edges 인자 = 검증된 인과만.
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

    _log("2", f"adding {len(nodes)} nodes with state_change/timestamp tooltips")
    for node in nodes:
        label = node.subject or node.id[:8]
        net.add_node(
            node.id,
            label=label,
            title=_node_tooltip(node),
            color="#4cc9f0",
            size=22,
        )

    # Step 3-3: CAUSES = verified only; orphan/rejected 데이터 없음
    _log("3", f"adding {len(edges)} verified CAUSES edges (arrows=to, rejected excluded)")
    for edge in edges:
        net.add_edge(
            edge.source_id,
            edge.target_id,
            title=_edge_tooltip(edge),
            label=f"{edge.probability:.2f}",
            color="#f72585",
            arrows="to",
            width=2 + edge.probability * 2,
        )

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
    """
    Step 3-5: HTML 파일 저장.

    Returns:
        resolve() 된 절대 경로.
    """
    net = build_pyvis_network(nodes, edges, title=title)
    output_path = output_path.resolve()
    _log("5", f"save_graph → {output_path}")
    net.save_graph(str(output_path))
    return output_path
