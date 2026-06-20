"""
Sprint 7 — batch warnings: partial_run, NG-2 (SP7-DEC-*, SP7-SKP-*).
"""

from __future__ import annotations

from typing import Any

NG2_NODE_THRESHOLD = 20


def collect_partial_run_warnings(pipeline_states: list[dict[str, Any]]) -> list[dict]:
    """DEC-01: one warning per run with partial_run=true."""
    warnings: list[dict] = []
    for idx, state in enumerate(pipeline_states, start=1):
        if not state.get("partial_run"):
            continue
        reason = str(state.get("partial_run_reason") or "unknown")
        meta = state.get("source_document_meta") or {}
        label = str(meta.get("source_file") or meta.get("chunk_id") or f"run-{idx}")
        warnings.append(
            {
                "code": "PARTIAL_RUN",
                "severity": "warn",
                "run_index": idx,
                "source_label": label,
                "reason": reason,
                "message": (
                    f"partial_run (run {idx}): {label} — "
                    f"비원자 crumb 잔존 ({reason}). 깊이 상한 도달."
                ),
            }
        )
    return warnings


def collect_ng2_warnings(
    *,
    node_count: int,
    skeleton: dict | None,
) -> list[dict]:
    """SKP-01: NG-2 — node count alone ≠ success; use Gap/Strong (AC-SKP-05)."""
    if not skeleton or node_count <= NG2_NODE_THRESHOLD:
        return []
    strong = skeleton.get("strong_chain_count", 0)
    gap = skeleton.get("gap_count", 0)
    if strong > 0 or gap > 0:
        return []
    return [
        {
            "code": "NG-2",
            "severity": "info",
            "node_count": node_count,
            "message": (
                f"NG-2: 그래프 노드 {node_count}개지만 Gap/Strong 지표 없음 — "
                "노드 수만으로 성공 판단 금지. Skeleton Health(Gap/Strong) 확인."
            ),
        }
    ]


def build_watch_report(
    *,
    pipeline_states: list[dict[str, Any]],
    skeleton: dict | None,
    node_count: int,
    ingest_violations: list[dict] | None = None,
) -> dict:
    """Aggregate watch payload for API/UI (SP7-API-01)."""
    warnings: list[dict] = []
    warnings.extend(collect_partial_run_warnings(pipeline_states))
    warnings.extend(collect_ng2_warnings(node_count=node_count, skeleton=skeleton))
    for v in ingest_violations or []:
        warnings.append({**v, "severity": "error", "code": v.get("code", "F0-A2")})

    partial_count = sum(1 for w in warnings if w.get("code") == "PARTIAL_RUN")
    return {
        "warnings": warnings,
        "warning_count": len(warnings),
        "partial_run_count": partial_count,
        "has_partial_run": partial_count > 0,
        "f0_a2_violations": list(ingest_violations or []),
        "blocking": bool(ingest_violations),
    }
