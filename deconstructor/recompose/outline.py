"""
Sprint 6 — ε-4 rewrite outline (SP6-OUT-01~02).
"""

from __future__ import annotations


def build_rewrite_outline(skeleton: dict) -> list[dict]:
    """
    Structured rewrite hints — not full LLM prose (NON-GOAL).

    - ``fix_gap``: high priority — add upstream 원인
    - ``keep``: strong claim to preserve
    - ``review_weak``: optional weak/hypothesis review
    """
    items: list[dict] = []

    for g in skeleton.get("gaps") or []:
        items.append(
            {
                "kind": "fix_gap",
                "priority": "high",
                "id": g.get("id"),
                "subject": g.get("subject", ""),
                "state_change": g.get("state_change", ""),
                "hint": (
                    f"Add upstream 원인 supporting «{g.get('subject', '?')}» "
                    f"→ {g.get('state_change', '')}"
                ),
            }
        )

    for o in skeleton.get("outline") or []:
        if o.get("role") != "strong":
            continue
        items.append(
            {
                "kind": "keep",
                "priority": "medium",
                "id": o.get("id"),
                "subject": o.get("subject", ""),
                "state_change": o.get("state_change", ""),
                "depth": o.get("depth", 0),
                "hint": "Preserve — part of verified strong chain",
            }
        )

    for w in skeleton.get("weak") or []:
        items.append(
            {
                "kind": "review_weak",
                "priority": "low",
                "id": w.get("id"),
                "subject": w.get("subject", ""),
                "state_change": w.get("state_change", ""),
                "hint": f"Review hypothesis: {w.get('reason', 'weak')}",
            }
        )

    return items
