"""
Neo4j → HTML보내기 및 기본 브라우저 자동 오픈
================================================

## 파이프라인 연동

  cli/modes/live.py, dry_traced.py 가 파이프라인 리포트 출력 **직후**
  maybe_visualize_after_pipeline(persist_db=...) 호출.

  --db 없으면 Neo4j에 쓰지 않으므로 viz 스킵.

## 출력 위치

  DEFAULT_OUTPUT = 프로젝트 루트 graph_output.html
  (deconstructor/viz/export.py 기준 parents[2])

## 다른 AI가 수정할 때

  - 브라우저 자동 오픈 끄려면: maybe_visualize_after_pipeline 에 플래그 추가하거나
    cli/parser.py 에 --no-viz 옵션 연결
  - viz 실패는 파이프라인 성공을 막지 않음 (try/except + 경고 출력)
"""

from __future__ import annotations

import webbrowser
from pathlib import Path

from deconstructor.viz.neo4j_fetch import fetch_full_graph
from deconstructor.viz.pyvis_render import render_to_html

# .../deconstructor/graph_output.html (gitignore 대상)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "graph_output.html"


def open_graph_in_browser(
    output_path: Path | None = None,
    *,
    title: str = "Deconstructor Causal Graph",
) -> Path:
    """
    Neo4j 전체 그래프 → HTML 저장 → 시스템 기본 브라우저에서 file:// URI 오픈.

    Args:
        output_path: None이면 DEFAULT_OUTPUT
        title: pyvis 페이지 제목

    Returns:
        저장된 HTML 절대 경로

    Side effects:
        webbrowser.open(), stdout [VIZ] 로그
    """
    out = output_path or DEFAULT_OUTPUT
    nodes, edges = fetch_full_graph()
    path = render_to_html(nodes, edges, out, title=title)

    uri = path.as_uri()
    webbrowser.open(uri)
    print(f"\n[VIZ] graph saved: {path}")
    print(f"[VIZ] opened in browser ({len(nodes)} nodes, {len(edges)} edges)")
    return path


def maybe_visualize_after_pipeline(*, persist_db: bool) -> None:
    """
    CLI 후처리 훅 — persist_db=True (--db) 일 때만 시각화.

    Neo4j 미사용 run 에서는 DB가 비어 있거나 stale 일 수 있으므로 스킵.
    예외는 삼켜서 파이프라인 exit code 0 유지.
    """
    if not persist_db:
        return
    try:
        open_graph_in_browser()
    except Exception as exc:
        print(f"\n[VIZ] could not open graph: {exc}")
