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
from deconstructor.storm.viz_style import DEFAULT_NODE_SIZE


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
  <button type="button" id="legend-toggle" aria-expanded="true">
    <span class="legend-title-chevron" aria-hidden="true"></span>
    <span class="legend-title-text">범례</span>
  </button>
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
      <li class="legend-size-row">
        <span class="swatch" style="background:{COLOR_EXTRACTED}"></span>
        <strong>크기</strong> — 모든 노드 동일 (원형)</li>
    </ul>

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
    <p class="legend-note">노랑·promoted hover → 원천(파랑) 쪽 <strong>초록 점선</strong> (anchor, 평소 숨김)</p>
    <p class="legend-note">파란 노드 <strong>우클릭</strong> → 내 가설 추가 (노란 pending, MVP)</p>
    <p class="legend-note"><strong>조작:</strong> 드래그로 이동 · 스크롤로 확대/축소</p>
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
  display: flex; align-items: center; gap: 6px;
}}
.legend-title-chevron {{
  display: none;
  flex-shrink: 0; width: 0; height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 6px solid #e8e8e8;
}}
.legend-title-text {{ flex: 0 0 auto; }}
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
  border-radius: 10px;
}}
#deconstructor-legend-wrap.legend-wrap-collapsed #legend-side-toggle {{
  display: none;
}}
#deconstructor-legend-wrap.legend-wrap-collapsed .legend-title-chevron {{
  display: block;
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

  function nodeBaselineOpacity(n) {{
    return n.opacity !== undefined && n.opacity !== null ? n.opacity : 1;
  }}

  function restoreNodeBaseline(n) {{
    var o = {{
      id: n.id,
      opacity: nodeBaselineOpacity(n),
    }};
    if (n.font) {{
      o.font = {{
        size: n.font.size,
        color: n.font.color,
        face: n.font.face,
        multi: n.font.multi,
        align: n.font.align,
        vadjust: n.font.vadjust,
      }};
    }}
    if (n.color) {{
      o.color = cloneData([n.color])[0];
    }}
    if (n.borderWidth !== undefined) o.borderWidth = n.borderWidth;
    return o;
  }}

  function restoreEdgeBaseline(e) {{
    return {{
      id: e.id,
      color: e.color ? cloneData([e.color])[0] : e.color,
      dashes: e.dashes,
      hidden: e.hidden,
      width: e.width,
    }};
  }}

  function nodeMatches(node, filter) {{
    if (filter === "hub") return false;
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
    var activeFilter = null;

    function captureBaseline() {{
      baselineNodes = cloneData(net.body.data.nodes.get());
      baselineEdges = cloneData(net.body.data.edges.get());
    }}

    function clearFilter() {{
      activeFilter = null;
      net.body.data.nodes.update(baselineNodes.map(restoreNodeBaseline));
      net.body.data.edges.update(baselineEdges.map(restoreEdgeBaseline));
      items.forEach(function(li) {{ li.classList.remove("legend-active"); }});
      if (typeof window.__dcSyncLabelZoom === "function") window.__dcSyncLabelZoom();
    }}

    function applyFilter(filter) {{
      activeFilter = filter;
      var isEdgeFilter = filter === "edge-solid" || filter === "edge-dashed";
      var nodeUpdates = baselineNodes.map(function(n) {{
        var keep = !isEdgeFilter && nodeMatches(n, filter);
        var u = {{ id: n.id, opacity: keep ? nodeBaselineOpacity(n) : DIM }};
        if (n.font) {{
          u.font = Object.assign({{}}, n.font);
          u.font.color = keep ? n.font.color : DIM_LABEL;
        }}
        return u;
      }});
      var edgeUpdates = baselineEdges.map(function(e) {{
        var keep = isEdgeFilter ? edgeMatches(e, filter) : false;
        if (keep) {{
          return restoreEdgeBaseline(e);
        }}
        return {{ id: e.id, color: dimEdgeColor(e), dashes: e.dashes }};
      }});
      net.body.data.nodes.update(nodeUpdates);
      net.body.data.edges.update(edgeUpdates);
    }}

    if (!items.length) return;

    // label zoom 이후 baseline 재캡처 (폰트 크기 drift 방지)
    setTimeout(captureBaseline, 800);
    setTimeout(captureBaseline, 2500);

    items.forEach(function(li) {{
      var filter = li.getAttribute("data-filter");
      if (!filter) return;
      li.addEventListener("mouseenter", function() {{
        li.classList.add("legend-active");
        applyFilter(filter);
      }});
      li.addEventListener("mouseleave", function(e) {{
        var legend = document.getElementById("deconstructor-legend");
        if (legend && e.relatedTarget && legend.contains(e.relatedTarget)) return;
        clearFilter();
      }});
    }});

    var legendRoot = document.getElementById("deconstructor-legend");
    if (legendRoot) {{
      legendRoot.addEventListener("mouseleave", function(e) {{
        if (e.relatedTarget && legendRoot.contains(e.relatedTarget)) return;
        clearFilter();
      }});
    }}

    var graphContainer = document.getElementById("mynetwork") || document.querySelector(".vis-network");
    if (graphContainer) {{
      graphContainer.addEventListener("mouseenter", function() {{
        if (activeFilter) clearFilter();
      }});
    }}
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
GRAPH_VIEWPORT_MARKER = "dcEnsureGraphViewport"
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
html, body {
  margin: 0 !important; padding: 0 !important;
  width: 100% !important;
  height: 100vh !important;
  min-height: 100vh !important;
  overflow: hidden !important;
  background: #1a1a2e !important;
}
body > center, body center:has(h1) { display: none !important; }
body > .card {
  width: 100% !important; height: 100vh !important; min-height: 100vh !important;
  margin: 0 !important; border: none !important;
  background: transparent !important;
}
#mynetwork {
  width: 100% !important;
  height: 100vh !important;
  min-height: 100vh !important;
  border: none !important;
  float: none !important;
  position: relative !important;
  background-color: #1a1a2e !important;
  padding: 0 !important;
}
#mynetwork.card-body { padding: 0 !important; }
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
    html_text = re.sub(
        r'<style type="text/css">.*?</style>\s*',
        "",
        html_text,
        count=1,
        flags=re.DOTALL,
    )
    html_text = re.sub(r"height:\s*800px", "height: 100vh", html_text)
    if "</head>" in html_text:
        debug_boot = """
<script id="dc-debug-boot">
if (location.search.indexOf("debug") >= 0) {
  function dcDebugShow(msg) {
    var dbg = document.getElementById("dc-debug-overlay");
    if (!dbg) {
      dbg = document.createElement("div");
      dbg.id = "dc-debug-overlay";
      dbg.style.cssText = "position:fixed;left:8px;bottom:8px;z-index:99999;background:rgba(0,0,0,.9);color:#7cfc00;font:12px monospace;padding:10px;line-height:1.5;pointer-events:none;max-width:92vw";
      (document.body || document.documentElement).appendChild(dbg);
    }
    dbg.innerHTML = msg;
  }
  window.__dcDebugShow = dcDebugShow;
  document.addEventListener("DOMContentLoaded", function() {
    dcDebugShow("debug: DOM ready, innerH=" + window.innerHeight + " (network loading...)");
  });
}
</script>
"""
        return html_text.replace("</head>", embed + debug_boot + "\n</head>", 1)
    return embed + html_text


def inject_graph_interaction(html_text: str) -> str:
    """pyvis HTML — 단순 viewport·fit·범례·anchor hover·우클릭 가설."""
    if GRAPH_INTERACTION_MARKER in html_text or GRAPH_VIEWPORT_MARKER in html_text:
        while GRAPH_VIEWPORT_MARKER in html_text:
            html_text = re.sub(
                r"\(function dcEnsureGraphViewport\(c\) \{.*?\}\)\(container\);\s*",
                "",
                html_text,
                count=1,
                flags=re.DOTALL,
            )
        while GRAPH_INTERACTION_MARKER in html_text:
            html_text = re.sub(
                r"\(function attachGraphInteraction\(net\) \{.*?\}\)\(network\);\s*",
                "",
                html_text,
                count=1,
                flags=re.DOTALL,
            )

    snippet = """
                  (function dcEnsureGraphViewport(c) {
                    function applySize() {
                      var h = Math.max(window.innerHeight || 0, 320);
                      document.documentElement.style.height = h + "px";
                      document.body.style.height = h + "px";
                      c.style.width = "100%";
                      c.style.height = h + "px";
                      return { w: c.clientWidth, h: h };
                    }
                    window.__dcApplyGraphViewport = applySize;
                    applySize();
                    window.addEventListener("resize", applySize);
                  })(container);
                  network = new vis.Network(container, data, options);
                  (function attachGraphInteraction(net) {
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
                          color: { color: "#90be6d", opacity: 0.92 },
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

                    function fitGraphView() {
                      try {
                        var dims = window.__dcApplyGraphViewport
                          ? window.__dcApplyGraphViewport()
                          : { w: container.clientWidth, h: container.clientHeight };
                        net.setSize(dims.w + "px", dims.h + "px");
                        net.fit({ padding: 40, animation: false });
                      } catch (e) {}
                    }
                    window.__dcFitGraphView = fitGraphView;
                    net.once("stabilizationIterationsDone", fitGraphView);
                    setTimeout(fitGraphView, 400);
                    window.addEventListener("message", function(ev) {
                      if (!ev.data || ev.data.type !== "deconstructor-resize") return;
                      fitGraphView();
                    });

                    (function attachHumanHypothesisUI(network) {
                      var modal = document.getElementById("dc-human-hypothesis-modal");
                      if (!modal) return;
                      var form = document.getElementById("dc-human-hypothesis-form");
                      var anchorLabel = document.getElementById("dc-hypothesis-anchor-label");
                      var statusEl = document.getElementById("dc-hypothesis-status");
                      var cancelBtn = document.getElementById("dc-hypothesis-cancel");
                      var pendingAnchorId = null;

                      function showModal(nodeId, nodeLabel) {
                        pendingAnchorId = nodeId;
                        anchorLabel.textContent = nodeLabel || nodeId;
                        statusEl.textContent = "";
                        modal.style.display = "flex";
                      }
                      function hideModal() {
                        modal.style.display = "none";
                        pendingAnchorId = null;
                        if (form) form.reset();
                      }
                      if (cancelBtn) cancelBtn.addEventListener("click", hideModal);
                      modal.addEventListener("click", function(e) {
                        if (e.target === modal) hideModal();
                      });

                      function pickExtractedNodeAtPointer(network, dom) {
                        var ptr = dom;
                        if (typeof network.DOMtoCanvas === "function") {
                          ptr = network.DOMtoCanvas(dom);
                        }
                        var ids = [];
                        if (typeof network.getNodesAt === "function") {
                          ids = network.getNodesAt(ptr) || [];
                        } else {
                          var one = network.getNodeAt(ptr);
                          if (one) ids = [one];
                        }
                        for (var i = 0; i < ids.length; i++) {
                          var n = network.body.data.nodes.get(ids[i]);
                          if (n && n.legend_class === "extracted") return { id: ids[i], node: n };
                        }
                        return null;
                      }

                      function onGraphContextMenu(e) {
                        var rect = container.getBoundingClientRect();
                        var dom = { x: e.clientX - rect.left, y: e.clientY - rect.top };
                        var hit = pickExtractedNodeAtPointer(network, dom);
                        if (!hit) return;
                        e.preventDefault();
                        e.stopPropagation();
                        showModal(hit.id, hit.node.label || "");
                      }

                      container.addEventListener("contextmenu", onGraphContextMenu, true);
                      var graphCanvas = container.querySelector("canvas");
                      if (graphCanvas) {
                        graphCanvas.addEventListener("contextmenu", onGraphContextMenu, true);
                      }

                      if (!form) return;
                      form.addEventListener("submit", function(e) {
                        e.preventDefault();
                        if (!pendingAnchorId) return;
                        statusEl.textContent = "저장 중…";
                        var body = {
                          anchor_fact_id: pendingAnchorId,
                          subject: document.getElementById("dc-hyp-subject").value.trim(),
                          state_change: document.getElementById("dc-hyp-state").value.trim(),
                          mechanism: document.getElementById("dc-hyp-mechanism").value.trim()
                        };
                        fetch("/api/human-hypothesis", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify(body)
                        })
                          .then(function(r) {
                            return r.json().then(function(j) {
                              return { httpOk: r.ok, j: j };
                            });
                          })
                          .then(function(res) {
                            if (!res.httpOk || res.j.ok === false) {
                              statusEl.textContent = res.j.error || "저장 실패";
                              return;
                            }
                            hideModal();
                            if (window.parent !== window) {
                              window.parent.postMessage(
                                { type: "deconstructor-graph-reload" },
                                "*"
                              );
                            }
                            window.location.reload();
                          })
                          .catch(function(err) {
                            statusEl.textContent = String(err);
                          });
                      });
                    })(net);
                  })(network);
"""
    return html_text.replace(
        "network = new vis.Network(container, data, options);",
        snippet,
        1,
    )


def inject_graph_chrome(html_text: str) -> str:
    """독립 탭(iframe 아님)용 전체 화면·메인 UI 링크."""
    html_text = re.sub(
        r'<div id="dc-graph-chrome".*?</script>\s*',
        "",
        html_text,
        count=1,
        flags=re.DOTALL,
    )
    chrome = """
<div id="dc-graph-chrome" style="display:none;position:fixed;top:10px;left:10px;z-index:100001;gap:8px;align-items:center;font-family:'Segoe UI',sans-serif;">
  <button type="button" id="dc-fs-btn" style="background:#1a73e8;color:#fff;border:none;border-radius:18px;padding:7px 14px;font-size:13px;cursor:pointer;">전체 화면</button>
  <a href="/" style="background:#fff;color:#1a73e8;border:1px solid #1a73e8;border-radius:18px;padding:6px 12px;font-size:13px;text-decoration:none;">메인 UI</a>
</div>
<script>
(function dcGraphChrome() {
  if (window.self !== window.top) return;
  var bar = document.getElementById("dc-graph-chrome");
  if (bar) bar.style.display = "flex";
  var fs = document.getElementById("dc-fs-btn");
  if (!fs) return;
  fs.addEventListener("click", function() {
    var el = document.documentElement;
    if (!document.fullscreenElement && el.requestFullscreen) el.requestFullscreen();
    else if (document.exitFullscreen) document.exitFullscreen();
  });
  document.addEventListener("fullscreenchange", function() {
    if (window.__dcApplyGraphViewport) window.__dcApplyGraphViewport();
    if (typeof window.__dcFitGraphView === "function") {
      setTimeout(function() { window.__dcFitGraphView(false, true, "fullscreen"); }, 200);
    }
  });
})();
</script>
"""
    if "</body>" in html_text:
        return html_text.replace("</body>", chrome + "\n</body>", 1)
    return html_text + chrome


def inject_human_hypothesis_modal(html_text: str) -> str:
    """
    사용자 가설 입력 모달 (MVP).

    ``attachHumanHypothesisUI`` (inject_graph_interaction) 와 id 를 맞춘다.
    Idempotent: 기존 블록 제거 후 재주입.
    """
    html_text = re.sub(
        r'<div id="dc-human-hypothesis-modal".*?</form>\s*</div>\s*',
        "",
        html_text,
        count=1,
        flags=re.DOTALL,
    )
    block = """
<div id="dc-human-hypothesis-modal" role="dialog" aria-labelledby="dc-hypothesis-title"
  style="display:none;position:fixed;inset:0;z-index:100002;background:rgba(0,0,0,.55);
  align-items:center;justify-content:center;font-family:'Segoe UI','Apple SD Gothic Neo',sans-serif;">
  <form id="dc-human-hypothesis-form"
    style="background:#1e1e2e;color:#e8e8e8;border-radius:12px;padding:20px 22px;width:min(420px,92vw);
    box-shadow:0 8px 32px rgba(0,0,0,.45);margin:16px;">
    <h2 id="dc-hypothesis-title" style="margin:0 0 4px;font-size:16px;font-weight:600;">가설 추가</h2>
    <p style="margin:0 0 14px;font-size:12px;color:#9aa0a6;line-height:1.45;">
      원천(파랑): <span id="dc-hypothesis-anchor-label"></span><br>
      Dreamer 가설과 동일하게 <strong>노란 pending</strong> 으로 저장됩니다 (MVP: 검증은 다음 단계).
    </p>
    <label style="display:block;font-size:12px;margin-bottom:4px;">주체 (subject)</label>
    <input id="dc-hyp-subject" required
      style="width:100%;box-sizing:border-box;margin-bottom:10px;padding:8px;border-radius:6px;border:1px solid #444;background:#2a2a3e;color:#fff;font-size:13px;">
    <label style="display:block;font-size:12px;margin-bottom:4px;">상태 변화 (state_change)</label>
    <input id="dc-hyp-state" required placeholder="예: increased, decreased"
      style="width:100%;box-sizing:border-box;margin-bottom:10px;padding:8px;border-radius:6px;border:1px solid #444;background:#2a2a3e;color:#fff;font-size:13px;">
    <label style="display:block;font-size:12px;margin-bottom:4px;">메커니즘 (선택)</label>
    <textarea id="dc-hyp-mechanism" rows="3"
      style="width:100%;box-sizing:border-box;margin-bottom:12px;padding:8px;border-radius:6px;border:1px solid #444;background:#2a2a3e;color:#fff;font-size:13px;resize:vertical;"></textarea>
    <p id="dc-hypothesis-status" style="min-height:1.2em;font-size:12px;color:#f4a261;margin:0 0 8px;"></p>
    <div style="display:flex;gap:8px;justify-content:flex-end;">
      <button type="button" id="dc-hypothesis-cancel"
        style="padding:8px 14px;border-radius:18px;border:1px solid #666;background:transparent;color:#ccc;cursor:pointer;font-size:13px;">취소</button>
      <button type="submit"
        style="padding:8px 16px;border-radius:18px;border:none;background:#1a73e8;color:#fff;cursor:pointer;font-size:13px;font-weight:500;">저장</button>
    </div>
  </form>
</div>
"""
    if "</body>" in html_text:
        return html_text.replace("</body>", block + "\n</body>", 1)
    return html_text + block


def inject_graph_filter_meta(html_text: str) -> str:
    """서버가 graph_output.html 을 낼 때 마지막 배치 필터를 JS 로 주입."""
    import json

    from deconstructor.web.graph_context import get_graph_filter_snapshot

    snap = get_graph_filter_snapshot()
    script = (
        "<script>window.__dcGraphFilter="
        + json.dumps(snap, ensure_ascii=False)
        + ";</script>\n"
    )
    if "</head>" in html_text:
        return html_text.replace("</head>", script + "</head>", 1)
    if "<body>" in html_text:
        return html_text.replace("<body>", "<body>\n" + script, 1)
    return script + html_text


def prepare_graph_html(html_text: str) -> str:
    """pyvis HTML → 범례·뷰포트·인터랙션·독립 탭 UI (메모리)."""
    text = inject_graph_embed_style(html_text)
    text = inject_graph_filter_meta(text)
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
    text = inject_human_hypothesis_modal(text)
    return inject_graph_chrome(text)


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
    text = prepare_graph_html(text)
    html_path.write_text(text, encoding="utf-8")
