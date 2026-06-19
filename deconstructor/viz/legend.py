"""
그래프 HTML 후처리 — 범례 패널 + vis.js 클릭 인터랙션
====================================================

Purpose / 목적
--------------
pyvis 가 생성한 ``graph_output.html`` 은 기본적으로 vis-network 만 포함한다.
이 모듈은 ``render_to_html`` 마지막 단계에서 파일을 읽어:

  1. ``inject_graph_interaction`` — ``network = new vis.Network(...)`` 직후
     physics freeze / drag pin 스크립트 삽입
  2. ``build_legend_html`` — 우측 상단 한국어 범례(노드색·CRITICAL·화살표·조작법)

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
from deconstructor.storm.viz_style import COLOR_CRITICAL, CRITICAL_NODE_SIZE, DEFAULT_NODE_SIZE


def build_legend_html() -> str:
    """
    pyvis graph_output.html ``</body>`` 앞에 삽입할 고정 범례 패널 HTML.

    CSS 는 인라인 ``<style>`` — 단일 파일 배포(graph_output.html)만으로 동작.
    ``#deconstructor-legend`` id 로 재주입 시 기존 패널 제거 가능.
    """
    return f"""
<div id="deconstructor-legend" lang="ko">
  <button type="button" id="legend-toggle" aria-expanded="true">범례 ▾</button>
  <div id="legend-body">
    <h3>노드 색 · 크기</h3>
    <ul class="legend-nodes">
      <li><span class="swatch" style="background:{COLOR_EXTRACTED}"></span>
        <strong>파랑</strong> — 추출(extracted): LLM이 원문에서 뽑은 사실</li>
      <li><span class="swatch" style="background:{COLOR_VERIFIED}"></span>
        <strong>초록</strong> — 검증(verified): Fact-Checker 통과·승격</li>
      <li><span class="swatch" style="background:{COLOR_INFERRED}"></span>
        <strong>노랑</strong> — 추론(inferred): Dreamer 가설·미검증</li>
      <li><span class="swatch faded" style="background:{COLOR_INFERRED}"></span>
        <strong>✖ 노랑(흐림)</strong> — 기각(dropped): Skeptic/Fact-Checker 거절</li>
      <li><span class="swatch large" style="background:{COLOR_CRITICAL}"></span>
        <strong>빨강·큼</strong> — CRITICAL: Perfect Storm (인과 누적 stress 또는 원인 2개+)</li>
      <li><span class="swatch" style="background:{COLOR_EXTRACTED}; box-shadow: 0 0 0 2px {COLOR_CRITICAL}"></span>
        <strong>빨간 테두리</strong> — CRITICAL 노드로 직접 인과되는 원인 (색은 provenance 유지)</li>
    </ul>
    <p class="legend-note">일반 노드 ≈ {DEFAULT_NODE_SIZE}px · CRITICAL ≈ {CRITICAL_NODE_SIZE}px</p>

    <h3>화살표 (인과 방향)</h3>
    <ul class="legend-edges">
      <li><span class="edge-line solid" style="background:{COLOR_EDGE_CAUSAL}"></span>
        <strong>분홍 실선</strong> — 검증된 인과 (CAUSES): <em>원인 → 결과</em></li>
      <li><span class="edge-line dashed"></span>
        <strong>노랑 점선</strong> — 가설·추론 연결 (미확정)</li>
    </ul>
    <p class="legend-note">화살표 hover → 원인·결과 시차(latency)</p>
    <p class="legend-note">노드 hover → subject, stress_level, timestamp 등</p>
    <p class="legend-note"><strong>조작:</strong> 노드 클릭 → 움직임 정지 · 드래그로 이동 · 빈 곳 더블클릭 → 다시 움직임</p>
  </div>
</div>
<style>
#deconstructor-legend {{
  position: fixed; top: 12px; right: 12px; z-index: 9999;
  max-width: 340px; font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif;
  font-size: 12px; line-height: 1.45; color: #e8e8e8;
  background: rgba(15, 15, 30, 0.92); border: 1px solid #444;
  border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,.45);
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
#deconstructor-legend li {{ display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; }}
.swatch {{
  flex-shrink: 0; width: 14px; height: 14px; border-radius: 50%; margin-top: 2px;
  border: 1px solid rgba(255,255,255,.3);
}}
.swatch.faded {{ opacity: 0.4; }}
.swatch.large {{ width: 20px; height: 20px; }}
.edge-line {{
  flex-shrink: 0; width: 28px; height: 3px; margin-top: 6px; border-radius: 2px;
}}
.edge-line.dashed {{
  background: repeating-linear-gradient(90deg, {COLOR_EDGE_HYPOTHESIS} 0 6px, transparent 6px 10px);
  height: 2px;
}}
.legend-note {{ margin: 4px 0 0; color: #9aa0a6; font-size: 11px; }}
.legend-note code {{ background: #2a2a3e; padding: 1px 4px; border-radius: 3px; }}
#deconstructor-legend.collapsed #legend-body {{ display: none; }}
</style>
<script>
(function() {{
  var btn = document.getElementById("legend-toggle");
  var box = document.getElementById("deconstructor-legend");
  if (btn && box) {{
    btn.addEventListener("click", function() {{
      var collapsed = box.classList.toggle("collapsed");
      btn.textContent = collapsed ? "범례 ▸" : "범례 ▾";
      btn.setAttribute("aria-expanded", String(!collapsed));
    }});
  }}
}})();
</script>
"""


# inject_graph_interaction 이 삽입한 IIFE 이름 — 재주입 시 제거용 마커
GRAPH_INTERACTION_MARKER = "attachGraphInteraction"


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
    text = inject_graph_interaction(text)
    if "deconstructor-legend" in text:
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
