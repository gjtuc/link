"""
Sprint 6 (G-REC-COMPOSE) — recompose_index orchestration (SP6-API-01).
"""

from __future__ import annotations

from deconstructor.recompose.narrative import build_verified_narrative
from deconstructor.recompose.outline import build_rewrite_outline
from deconstructor.recompose.report import build_health_report
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode


def recompose_index(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    skeleton: dict,
    *,
    fact_checker: dict | None = None,
    items_processed: int = 0,
) -> dict:
    """
    Post-pipeline recompose bundle (ε-2~4).

    Returns JSON-serializable dict for analyze result / ``GET /api/recompose``.
    """
    report_md = build_health_report(skeleton, fact_checker=fact_checker)
    narrative = build_verified_narrative(nodes, edges, skeleton)
    rewrite_outline = build_rewrite_outline(skeleton)

    return {
        "report_markdown": report_md,
        "verified_narrative": narrative,
        "rewrite_outline": rewrite_outline,
        "outline_count": len(rewrite_outline),
        "has_strong_narrative": narrative
        and not narrative.startswith("(No verified"),
        "items_processed": items_processed,
        "epsilon": {
            "e2_report": True,
            "e3_narrative": True,
            "e4_rewrite_outline": True,
        },
    }
