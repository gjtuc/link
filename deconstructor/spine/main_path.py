"""
STAGE 0-SPINE — μ-SPINE-02
계약: docs/design/BRANCH-SPINE-spec.md
철학: §1f 주 경로 — CAUSES-only 최장 경로
"""

from __future__ import annotations

from collections import defaultdict


def longest_causes_path(
    node_ids: set[str],
    causes_edges: list[tuple[str, str]],
) -> list[str]:
    """Longest simple path using CAUSES edges only (tie: lexicographically earlier start)."""
    if not node_ids:
        return []
    adj: dict[str, list[str]] = defaultdict(list)
    for source, target in causes_edges:
        if source in node_ids and target in node_ids:
            adj[source].append(target)

    best: list[str] = []
    for start in sorted(node_ids):
        stack: list[tuple[str, list[str]]] = [(start, [start])]
        while stack:
            current, path = stack.pop()
            if len(path) > len(best) or (len(path) == len(best) and path < best):
                best = path
            for nxt in adj.get(current, []):
                if nxt in path:
                    continue
                stack.append((nxt, path + [nxt]))
    return best
