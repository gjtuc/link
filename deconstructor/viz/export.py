"""
Step 4 — 브라우저 자동화 및 파이프라인 결합 (Micro-step)
========================================================

Micro-steps ([VIZ-S4-...] 로그):
  S4-1  persist_db / --db 가드
  S4-2  Step 2 fetch_causal_graph()
  S4-3  Step 3 render_to_html()
  S4-4  webbrowser.open(file://...)
  S4-5  완료 요약

main.py 마지막에서 maybe_visualize_after_pipeline() 호출.
"""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path

from deconstructor.viz.neo4j_utils import fetch_causal_graph
from deconstructor.viz.visualizer import render_to_html

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "graph_output.html"


def _log(step: str, msg: str) -> None:
    line = f"[VIZ-S4-{step}] {msg}"
    logger.info(line)
    print(line)


def open_graph_in_browser(
    output_path: Path | None = None,
    *,
    title: str = "Deconstructor Causal Graph",
    max_nodes: int = 300,
) -> Path:
    """
    End-to-end: Neo4j fetch → pyvis HTML → 기본 브라우저 오픈.

    Args:
        output_path: None이면 프로젝트 루트 graph_output.html
        max_nodes: Step 2 노드 상한 (기본 300)
    """
    out = output_path or DEFAULT_OUTPUT

    _log("2", "start fetch_causal_graph (Step 2)")
    fetched = fetch_causal_graph(max_nodes=max_nodes)
    if fetched.truncated:
        _log(
            "2",
            f"WARNING truncated: showing {len(fetched.nodes)}/{fetched.total_nodes_in_db} nodes",
        )

    _log("3", f"start render_to_html → {out} (Step 3)")
    path = render_to_html(fetched.nodes, fetched.edges, out, title=title)

    _log("4", f"webbrowser.open {path.as_uri()}")
    webbrowser.open(path.as_uri())

    _log(
        "5",
        f"done nodes={len(fetched.nodes)} edges={len(fetched.edges)} "
        f"file={path}",
    )
    print(f"\n[VIZ] graph saved: {path}")
    print(
        f"[VIZ] opened in browser "
        f"({len(fetched.nodes)} nodes, {len(fetched.edges)} verified edges)"
    )
    return path


def maybe_visualize_after_pipeline(*, persist_db: bool) -> None:
    """
    main.py 후처리 훅 — --db 로 Neo4j에 썼을 때만 Step 2~4 실행.

    파이프라인 실패(exit!=0) 시 main.py 에서 호출하지 않음.
    """
    if not persist_db:
        _log("1", "skip: persist_db=False (--db not set)")
        return

    _log("1", "persist_db=True → running end-to-end visualization")
    try:
        open_graph_in_browser()
    except Exception as exc:
        print(f"\n[VIZ] could not open graph: {exc}")
