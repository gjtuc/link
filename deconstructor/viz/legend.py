"""
그래프 HTML 후처리 — 범례 패널 + vis.js 클릭 인터랙션
====================================================

Purpose / 목적
--------------
pyvis 가 생성한 ``graph_output.html`` 은 기본적으로 vis-network 만 포함한다.
이 모듈은 ``render_to_html`` 마지막 단계에서 파일을 읽어:

  1. ``inject_graph_interaction`` — ``network = new vis.Network(...)`` 직후
     physics freeze / drag pin 스크립트 삽입
  2. ``build_legend_html`` — 우측 상단 한국어 범례(노드색·크기·화살표·조작법)

Pipeline position / 파이프라인 위치
---------------------------------
  visualizer.render_to_html  →  net.save_graph  →  **inject_legend_into_html**

Why post-process instead of pyvis template?
-------------------------------------------
pyvis 는 ``Network`` 생성 시 커스텀 JS 훅이 제한적이다.
``drawGraph()`` 내부 ``network`` 지역 변수에 접근하려면
생성 직후 IIFE 를 문자열 replace 로 끼워 넣는 방식이 가장 안정적이다.
재렌더 시 기존 범례/스크립트는 regex 로 제거 후 다시 주입(idempotent).

Interaction script (attachGraphInteraction)
-------------------------------------------
  - click / dragStart on node → ``physics.enabled=false``, edge smooth → continuous
  - dragEnd → ``fixed:{x,y:true}`` 로 노드 위치 고정 (마우스 따라가기)
  - doubleClick on empty canvas → physics 재개, 모든 노드 fixed 해제
  - **hoverNode / blurNode** — ``anchor_hover_only`` 점선 표시 (Dreamer 원천→가설)
  - 범례 기호 hover → ``__dcAttachLegendHighlight`` (해당 색·엣지만 강조)

Post-inject CSS (inject_graph_embed_style)
------------------------------------------
  - pyvis 중복 ``<h1>`` 숨김 (제목은 Link UI 전체화면 바)
  - ``#mynetwork`` 높이 100% · ``div.vis-tooltip`` ``pre-line`` (한국어 툴팁)

Legend content sync
-------------------
범례 문구는 visualizer.py 의 실제 스타일과 맞춰야 한다.
변경 시: provenance/viz_style, storm/viz_style 상수 + visualizer 로직 동시 갱신.

When to modify / 수정 시점
--------------------------
- pyvis 버전 업으로 ``network = new vis.Network(container, data, options);`` 문자열 변경 시
  ``inject_graph_interaction`` 의 replace 대상 확인
- vis.js API 변경 시 freeze/unfreeze setOptions 키 검증
"""

from __future__ import annotations

import re
from pathlib import Path

from deconstructor.provenance.viz_style import (
    COLOR_EDGE_CAUSAL,
    COLOR_EDGE_HYPOTHESIS,
    COLOR_EXTRACTED,
    COLOR_INFERRED,
    COLOR_VERIFIED,
)
from deconstructor.storm.viz_style import DEFAULT_NODE_SIZE, MAX_NODE_SIZE


def build_legend_html() -> str:
    """
    pyvis graph_output.html ``</body>`` 앞에 삽입할 고정 범례 패널 HTML.

    CSS 는 인라인 ``<style>`` — 단일 파일 배포(graph_output.html)만으로 동작.
    ``#deconstructor-legend`` id 로 재주입 시 기존 패널 제거 가능.
    """
    return f"""
<div id="deconstructor-legend-wrap">
  <button type="button" id="legend-side-toggle" aria-expanded="true"
    aria-label="범례 접기" title="범례 접기">
    <span class="legend-side-icon" aria-hidden="true"></span>
  </button>
  <div id="deconstructor-legend" lang="ko">
  <button type="button" id="legend-toggle" aria-expanded="true">범례 ▾</button>
  <div id="legend-body">
    <h3>노드 색 · 크기</h3>
    <ul class="legend-nodes">
      <li class="legend-filter-item" data-filter="extracted">
        <span class="swatch" style="background:{COLOR_EXTRACTED}"></span>
        <strong>파랑</strong> — 추출(extracted): LLM이 원문에서 뽑은 사실</li>
      <li class="legend-filter-item" data-filter="verified">
        <span class="swatch" style="background:{COLOR_VERIFIED}"></span>
        <strong>초록</strong> — 검증(verified): 외부·원문 기반 확정 사실</li>
      <li class="legend-filter-item" data-filter="inferred">
        <span class="swatch" style="background:{COLOR_INFERRED}"></span>
        <strong>노랑</strong> — 추론(inferred·pending): Dreamer(추론가) 가설·미검증</li>
      <li class="legend-filter-item" data-filter="promoted">
        <span class="swatch" style="background:{COLOR_INFERRED}; box-shadow: 0 0 0 3px {COLOR_VERIFIED}"></span>
        <strong>노랑+초록 테두리</strong> — 추론가 가설이 Fact-Checker 통과 (promoted)</li>
      <li class="legend-filter-item" data-filter="dropped">
        <span class="swatch faded" style="background:{COLOR_INFERRED}"></span>
        <strong>✖ 노랑(흐림)</strong> — 기각(dropped): Fact-Checker/Skeptic 거절</li>
      <li class="legend-filter-item legend-size-row" data-filter="hub">
        <span class="swatch" style="background:{COLOR_EXTRACTED}"></span>
        <span class="swatch large" style="background:{COLOR_EXTRACTED}"></span>
        <strong>크기</strong> — CAUSES 연결이 많을수록 노드가 커짐 (색은 provenance 유지)</li>
    </ul>
    <p class="legend-note">기본 ≈ {DEFAULT_NODE_SIZE}px · 연결 hub 최대 ≈ {MAX_NODE_SIZE}px</p>

    <h3>화살표 (인과 방향)</h3>
    <ul class="legend-edges">
      <li class="legend-filter-item" data-filter="edge-solid">
        <span class="edge-line solid" style="background:{COLOR_EDGE_CAUSAL}"></span>
        <strong>회색 실선</strong> — 검증된 인과 (CAUSES): <em>원인 → 결과</em></li>
      <li class="legend-filter-item" data-filter="edge-dashed">
        <span class="edge-line dashed"></span>
        <strong>연한 회색 점선</strong> — 가설·미검증 추론 연결 (pending/dropped)</li>
    </ul>
    <p class="legend-note">범례 기호에 마우스를 올리면 해당 노드·화살표만 강조됩니다</p>
    <p class="legend-note">promoted(초록 테두리) 노드로 이어지는 인과는 <strong>회색 실선</strong></p>
    <p class="legend-note">화살표 hover → 원인·결과 시차(latency)</p>
    <p class="legend-note">노랑·promoted hover → 원천(파랑) 쪽 <strong>초록 점선</strong> (Dreamer anchor, 평소 숨김)</p>
    <p class="legend-note"><strong>조작:</strong> 노드 클릭 → 움직임 정지 · 드래그로 이동 · 빈 곳 더블클릭 → 다시 움직임</p>
  </div>
  </div>
</div>
<style>
#deconstructor-legend-wrap {{
  position: fixed; top: 12px; right: 12px; z-index: 9999;
  display: flex; flex-direction: row; align-items: flex-start;
  max-width: 364px;
}}
#legend-side-toggle {{
  flex-shrink: 0; width: 20px; height: 20px; margin-top: 10px; padding: 0;
  border: 1px solid #555; border-right: none;
  border-radius: 6px 0 0 6px;
  background: rgba(15, 15, 30, 0.94); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: #e8e8e8;
}}
#legend-side-toggle:hover {{ background: rgba(35, 35, 55, 0.98); }}
#legend-side-toggle:focus-visible {{
  outline: 2px solid #8ecae6; outline-offset: 1px;
}}
.legend-side-icon {{
  display: block; width: 0; height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 5px solid #e8e8e8;
  transition: transform 0.15s ease;
}}
#deconstructor-legend-wrap.legend-wrap-collapsed .legend-side-icon {{
  transform: rotate(180deg);
}}
#deconstructor-legend {{
  flex: 1; min-width: 0; max-width: 340px;
  font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif;
  font-size: 12px; line-height: 1.45; color: #e8e8e8;
  background: rgba(15, 15, 30, 0.92); border: 1px solid #444;
  border-radius: 0 10px 10px 10px; box-shadow: 0 4px 20px rgba(0,0,0,.45);
}}
#deconstructor-legend h3 {{
  margin: 0 0 6px; font-size: 12px; font-weight: 600; color: #fff;
}}
#legend-toggle {{
  width: 100%; text-align: left; padding: 10px 12px;
  background: transparent; border: none; color: #fff;
  font-size: 13px; font-weight: 600; cursor: pointer;
}}
#legend-body {{ padding: 0 12px 12px; }}
#deconstructor-legend ul {{ margin: 0 0 10px; padding: 0; list-style: none; }}
#deconstructor-legend li {{
  display: flex; align-items: center; gap: 10px; margin-bottom: 4px;
  padding: 6px 8px; border-radius: 8px; cursor: default;
  transition: background 0.12s ease;
}}
.legend-filter-item:hover, .legend-filter-item.legend-active {{
  background: rgba(255,255,255,0.1);
}}
.swatch {{
  flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%; margin-top: 0;
  border: 1px solid rgba(255,255,255,.35);
  pointer-events: none;
}}
.swatch.faded {{ opacity: 0.4; }}
.swatch.large {{ width: 32px; height: 32px; }}
.legend-size-row .swatch + .swatch {{ margin-left: -4px; }}
.edge-line {{
  flex-shrink: 0; width: 44px; height: 5px; margin-top: 0; border-radius: 2px;
  pointer-events: none;
}}
.edge-line.dashed {{
  background: repeating-linear-gradient(90deg, {COLOR_EDGE_HYPOTHESIS} 0 8px, transparent 8px 13px);
  height: 4px;
}}
.legend-note {{ margin: 4px 0 0; color: #9aa0a6; font-size: 11px; }}
.legend-note code {{ background: #2a2a3e; padding: 1px 4px; border-radius: 3px; }}
#deconstructor-legend-wrap.legend-wrap-collapsed #legend-body {{ display: none; }}
#deconstructor-legend-wrap.legend-wrap-collapsed #deconstructor-legend {{
  border-radius: 0 10px 10px 0;
}}
#deconstructor-legend-wrap.legend-wrap-collapsed #legend-side-toggle {{
  border-right: 1px solid #555;
  border-radius: 6px 0 0 6px;
}}
</style>
<script>
(function() {{
  var DIM = {LEGEND_DIM_OPACITY};
  var DIM_LABEL = "{LEGEND_DIM_LABEL_RGBA}";

  function cloneData(items) {{
    return JSON.parse(JSON.stringify(items));
  }}

  function dimEdgeColor(edge) {{
    if (!edge.color) return {{ color: "rgba(184,193,204," + DIM + ")" }};
    if (typeof edge.color === "string") {{
      return {{ color: edge.color, opacity: DIM }};
    }}
    return {{
      color: edge.color.color || edge.color,
      opacity: DIM,
      highlight: edge.color.highlight,
      hover: edge.color.hover
    }};
  }}

  function nodeMatches(node, filter) {{
    if (filter === "hub") return node.legend_hub === true;
    if (filter === "edge-solid" || filter === "edge-dashed") return false;
    return node.legend_class === filter;
  }}

  function edgeMatches(edge, filter) {{
    if (filter === "edge-solid" || filter === "edge-dashed") {{
      return edge.legend_class === filter;
    }}
    return false;
  }}

  window.__dcAttachLegendHighlight = function(net) {{
    if (!net || net.__dcLegendAttached) return;
    net.__dcLegendAttached = true;

    var baselineNodes = cloneData(net.body.data.nodes.get());
    var baselineEdges = cloneData(net.body.data.edges.get());
    var items = document.querySelectorAll("#deconstructor-legend .legend-filter-item");
    if (!items.length) return;

    function clearFilter() {{
      net.body.data.nodes.update(cloneData(baselineNodes));
      net.body.data.edges.update(cloneData(baselineEdges));
      items.forEach(function(li) {{ li.classList.remove("legend-active"); }});
    }}

    function applyFilter(filter) {{
      var isEdgeFilter = filter === "edge-solid" || filter === "edge-dashed";
      var nodeUpdates = baselineNodes.map(function(n) {{
        var keep = !isEdgeFilter && nodeMatches(n, filter);
        var u = {{ id: n.id, opacity: keep ? (n.opacity !== undefined ? n.opacity : 1) : DIM }};
        if (n.font) {{
          u.font = Object.assign({{}}, n.font);
          u.font.color = keep ? n.font.color : DIM_LABEL;
        }}
        return u;
      }});
      var edgeUpdates = baselineEdges.map(function(e) {{
        var keep = isEdgeFilter ? edgeMatches(e, filter) : false;
        if (keep) {{
          return {{ id: e.id, color: e.color, dashes: e.dashes }};
        }}
        return {{ id: e.id, color: dimEdgeColor(e), dashes: e.dashes }};
      }});
      net.body.data.nodes.update(nodeUpdates);
      net.body.data.edges.update(edgeUpdates);
    }}

    items.forEach(function(li) {{
      var filter = li.getAttribute("data-filter");
      if (!filter) return;
      li.addEventListener("mouseenter", function() {{
        li.classList.add("legend-active");
        applyFilter(filter);
      }});
      li.addEventListener("mouseleave", clearFilter);
    }});
  }};

  if (window.__dcGraphNetwork) {{
    window.__dcAttachLegendHighlight(window.__dcGraphNetwork);
  }}

  var btn = document.getElementById("legend-toggle");
  var sideBtn = document.getElementById("legend-side-toggle");
  var wrap = document.getElementById("deconstructor-legend-wrap");
  var box = document.getElementById("deconstructor-legend");

  function setLegendCollapsed(collapsed) {{
    if (!wrap || !box || !btn) return;
    wrap.classList.toggle("legend-wrap-collapsed", collapsed);
    box.classList.toggle("collapsed", collapsed);
    btn.textContent = collapsed ? "범례 ▸" : "범례 ▾";
    btn.setAttribute("aria-expanded", String(!collapsed));
    if (sideBtn) {{
      sideBtn.setAttribute("aria-expanded", String(!collapsed));
      sideBtn.setAttribute("aria-label", collapsed ? "범례 펼치기" : "범례 접기");
      sideBtn.setAttribute("title", collapsed ? "범례 펼치기" : "범례 접기");
    }}
  }}

  function toggleLegend() {{
    if (!box) return;
    setLegendCollapsed(!box.classList.contains("collapsed"));
  }}

  if (btn && box) {{
    btn.addEventListener("click", toggleLegend);
  }}
  if (sideBtn) {{
    sideBtn.addEventListener("click", toggleLegend);
  }}
}})();
</script>
"""


# inject_graph_interaction 이 삽입한 IIFE 이름 — 재주입 시 제거용 마커
GRAPH_EMBED_STYLE_MARKER = "deconstructor-graph-embed"
GRAPH_INTERACTION_MARKER = "attachGraphInteraction"
LEGEND_HIGHLIGHT_MARKER = "attachLegendHighlight"

# 범례 hover 시 비일치 요소 opacity (0–1)
LEGEND_DIM_OPACITY = 0.13
LEGEND_DIM_LABEL_RGBA = "rgba(232,232,232,0.14)"


def inject_graph_embed_style(html_text: str) -> str:
    """
    pyvis embed CSS — 제목 숨김, 그래프·툴팁 레이아웃.

    Idempotent: ``#deconstructor-graph-embed`` 블록 제거 후 재주입.
    """
    html_text = re.sub(
        r'<style id="deconstructor-graph-embed">.*?</style>\s*',
        "",
        html_text,
        count=1,
        flags=re.DOTALL,
    )
    embed = """
<style id="deconstructor-graph-embed">
html, body { margin: 0 !important; padding: 0 !important; height: 100% !important; }
body > center, body center:has(h1) { display: none !important; }
#mynetwork {
  width: 100% !important;
  height: 100% !important;
  min-height: 420px !important;
  border: none !important;
  float: none !important;
}
div.vis-tooltip {
  white-space: pre-line !important;
  max-width: 380px !important;
  font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif !important;
  font-size: 12px !important;
  line-height: 1.45 !important;
  padding: 8px 10px !important;
}
</style>
"""
    if "</head>" in html_text:
        return html_text.replace("</head>", embed + "\n</head>", 1)
    return embed + html_text


def inject_graph_interaction(html_text: str) -> str:
    """
    pyvis HTML — 노드 클릭 시 physics 정지 + 드래그 pin.

    pyvis ``templates/template.html`` 의 drawGraph() 가 내보내는 한 줄:
      ``network = new vis.Network(container, data, options);``
    을 찾아, network 생성 + attachGraphInteraction IIFE 로 치환한다.

    Idempotent: GRAPH_INTERACTION_MARKER 가 이미 있으면 기존 IIFE 를 regex 제거 후
    다시 삽입 (legend 재생성·visualizer 재실행 대응).

    Args:
        html_text: graph_output.html 전체 문자열

    Returns:
        interaction 스크립트가 포함된 HTML
    """
    if GRAPH_INTERACTION_MARKER in html_text:
        html_text = re.sub(
            r"\(function attachGraphInteraction\(net\) \{.*?\}\)\(network\);\s*",
            "",
            html_text,
            count=1,
            flags=re.DOTALL,
        )

    # vis-network: physics 끄면 dynamic edge smooth 가 덜 흔들림
    snippet = """
                  network = new vis.Network(container, data, options);
                  (function attachGraphInteraction(net) {
                    var physicsFrozen = false;
                    function freezePhysics() {
                      if (physicsFrozen) return;
                      physicsFrozen = true;
                      net.setOptions({
                        physics: { enabled: false },
                        edges: { smooth: { type: "continuous" } }
                      });
                    }
                    function unfreezePhysics() {
                      if (!physicsFrozen) return;
                      physicsFrozen = false;
                      var ids = net.body.data.nodes.getIds();
                      var updates = ids.map(function(id) {
                        return { id: id, fixed: false };
                      });
                      net.body.data.nodes.update(updates);
                      net.setOptions({
                        physics: { enabled: true },
                        edges: { smooth: { type: "dynamic" } }
                      });
                    }
                    net.on("click", function(params) {
                      if (params.nodes && params.nodes.length) freezePhysics();
                    });
                    net.on("dragStart", function(params) {
                      if (params.nodes && params.nodes.length) freezePhysics();
                    });
                    net.on("dragEnd", function(params) {
                      if (!params.nodes || !params.nodes.length) return;
                      var id = params.nodes[0];
                      var pos = net.getPositions([id])[id];
                      net.body.data.nodes.update({
                        id: id,
                        x: pos.x,
                        y: pos.y,
                        fixed: { x: true, y: true }
                      });
                    });
                    net.on("doubleClick", function(params) {
                      var empty = (!params.nodes || !params.nodes.length)
                        && (!params.edges || !params.edges.length);
                      if (empty) unfreezePhysics();
                    });

                    var ANCHOR_EDGE_COLOR = "#90be6d";
                    function hideAnchorHintEdges() {
                      var edges = net.body.data.edges.get({
                        filter: function(e) { return e.anchor_hover_only === true; }
                      });
                      if (!edges.length) return;
                      net.body.data.edges.update(edges.map(function(e) {
                        return { id: e.id, hidden: true };
                      }));
                    }
                    function showAnchorHintForNode(nodeId) {
                      var node = net.body.data.nodes.get(nodeId);
                      if (!node || !node.anchor_fact_id) return;
                      var edges = net.body.data.edges.get({
                        filter: function(e) {
                          return e.anchor_hover_only === true
                            && e.from === node.anchor_fact_id
                            && e.to === nodeId;
                        }
                      });
                      if (!edges.length) return;
                      hideAnchorHintEdges();
                      net.body.data.edges.update(edges.map(function(e) {
                        return {
                          id: e.id,
                          hidden: false,
                          color: { color: ANCHOR_EDGE_COLOR, opacity: 0.92 },
                          width: 2.5
                        };
                      }));
                    }
                    net.on("hoverNode", function(params) {
                      hideAnchorHintEdges();
                      if (params.node) showAnchorHintForNode(params.node);
                    });
                    net.on("blurNode", hideAnchorHintEdges);

                    window.__dcGraphNetwork = net;
                    if (typeof window.__dcAttachLegendHighlight === "function") {
                      window.__dcAttachLegendHighlight(net);
                    }
                  })(network);
"""
    return html_text.replace(
        "network = new vis.Network(container, data, options);",
        snippet,
        1,
    )


def inject_legend_into_html(html_path: Path) -> None:
    """
    저장된 pyvis HTML 파일에 범례 + 클릭 고정 인터랙션을 주입 (in-place write).

    호출 순서:
      1. inject_graph_interaction (본문)
      2. 기존 #deconstructor-legend 블록 제거 (있으면)
      3. </body> 직전에 build_legend_html() 삽입

    Args:
        html_path: 보통 ``ROOT/graph_output.html``
    """
    text = html_path.read_text(encoding="utf-8")
    text = inject_graph_embed_style(text)
    text = inject_graph_interaction(text)
    if "deconstructor-legend" in text:
        text = re.sub(
            r'<div id="deconstructor-legend-wrap".*?</script>\s*',
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        if "deconstructor-legend-wrap" not in text:
            text = re.sub(
                r'<div id="deconstructor-legend".*?</script>\s*',
                "",
                text,
                count=1,
                flags=re.DOTALL,
            )
    legend = build_legend_html()
    if "</body>" in text:
        text = text.replace("</body>", legend + "\n</body>", 1)
    else:
        text += legend
    html_path.write_text(text, encoding="utf-8")
