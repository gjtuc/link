"""
Sprint 3 (G-DEC-DENS) — min facts hint from ingest text length.

See ``docs/design/SPRINT-3-deconstruct-depth-spec.md`` (μ PRM-03).
"""

from __future__ import annotations


def min_facts_for_text(text: str) -> int:
    """Suggest minimum FactList size for document-length inputs (AC-DEC-02 SHOULD)."""
    n = len((text or "").strip())
    if n < 500:
        return 2
    if n < 2000:
        return 3
    if n < 8000:
        return 5
    return 8


def density_hint_line(text: str) -> str:
    """Optional user-prompt appendix (empty for very short text)."""
    minimum = min_facts_for_text(text)
    if minimum <= 2:
        return ""
    return (
        f"\n- This input is ~{len(text.strip())} characters; "
        f"extract at least {minimum} distinct facts when the text supports it.\n"
        f"- Prefer several atomic facts over one summary fact.\n"
    )
