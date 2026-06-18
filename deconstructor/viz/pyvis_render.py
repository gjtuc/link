"""
pyvis 인터랙티브 인과 그래프 HTML 생성
======================================

## 역할

GraphNode/GraphEdge → pyvis.Network → 단일 HTML 파일.

## UX 요구사항 (사용자 스펙)

  - 노드 hover: subject, state_change, timestamp, headline(trigger_event) 툴팁
  - 엣지 hover: probability, latency
  - physics enabled: Barnes-Hut + damping 으로 드래그 시 쫀득한 움직임

## 다른 AI가 수정할 때

  - vis.js 옵션은 net.set_options() JSON 문자열 — pyvis 버전별 호환 확인
  - 색/크기는 가독성용; 비즈니스 로직 없음
  - 대용량 그래프(수백 노드)면 stabilization iterations 조정
"""

from __future__ import annotations

from pathlib import Path

from pyvis.network import Network

from deconstructor.viz.neo4j_fetch import GraphEdge, GraphNode


def _node_tooltip(node: GraphNode) -> str:
    """
    vis.js title 필드 (HTML <br> 구분).

    마우스 오버 시 브라우저 기본 툴팁으로 표시됨.
    """
    lines = [
        f"subject: {node.subject}",
        f"state_change: {node.state_change}",
        f"timestamp: {node.timestamp or 'n/a'}",
    ]
    if node.trigger_event:
        preview = node.trigger_event[:120]
        if len(node.trigger_event) > 120:
            preview += "..."
        lines.append(f"headline: {preview}")
    return "<br>".join(lines)


def _edge_tooltip(edge: GraphEdge) -> str:
    """CAUSES 관계 메타데이터 툴팁."""
    latency = f"{edge.latency} ms" if edge.latency is not None else "n/a"
    return f"probability: {edge.probability:.3f}<br>latency: {latency}"


def build_pyvis_network(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    title: str = "Deconstructor Causal Graph",
) -> Network:
    """
    pyvis Network 객체 구성 (아직 파일 저장 전).

    Args:
        nodes: fetch_full_graph() 결과
        edges: fetch_full_graph() 결과
        title: HTML 페이지 상단 제목

    Returns:
        설정 완료된 Network (save_graph 호출 전).
    """
    net = Network(
        height="800px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#e8e8e8",
        directed=True,
        heading=title,
    )

    for node in nodes:
        label = node.subject or node.id[:8]
        net.add_node(
            node.id,
            label=label,
            title=_node_tooltip(node),
            color="#4cc9f0",
            size=22,
        )

    for edge in edges:
        net.add_edge(
            edge.source_id,
            edge.target_id,
            title=_edge_tooltip(edge),
            label=f"{edge.probability:.2f}",
            color="#f72585",
            arrows="to",
            # probability 높을수록 시각적으로 두꺼운 화살표
            width=2 + edge.probability * 2,
        )

    # vis.js 물리·인터랙션 옵션 (JSON 문자열로 주입)
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
    "smooth": { "type": "dynamic" }
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
    HTML 파일로 저장.

    Args:
        output_path: 예) 프로젝트 루트 graph_output.html

    Returns:
        resolve() 된 절대 경로 (webbrowser.open(file://...) 용).
    """
    net = build_pyvis_network(nodes, edges, title=title)
    output_path = output_path.resolve()
    net.save_graph(str(output_path))
    return output_path
