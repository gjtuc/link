"""
Sprint 3 (G-DEC-RECUR) — compound crumb heuristic before verify partition.

See ``docs/design/SPRINT-3-deconstruct-depth-spec.md`` (μ HEU-*).

Conservative: only downgrade is_atomic True → False when compound markers detected.
Never force atomic True (NG-2 / false splits).
"""

from __future__ import annotations

from deconstructor.models import AtomicFact

_COMPOUND_SUBJECT_MARKERS = (" and ", " & ", ", ", " / ")
_COMPOUND_STATE_MARKERS = (" and ", ";")


def looks_compound(fact: AtomicFact) -> bool:
    """True if fact likely combines multiple entities/steps (μ HEU-01)."""
    if not fact.is_atomic:
        return False
    subj = (fact.subject or "").lower()
    st = (fact.state_change or "").lower()
    if any(m in subj for m in _COMPOUND_SUBJECT_MARKERS):
        return True
    if any(m in st for m in _COMPOUND_STATE_MARKERS):
        return True
    return False


def apply_compound_heuristic(facts: list[AtomicFact]) -> list[AtomicFact]:
    """Downgrade mis-flagged atomic facts so verify routes back to deconstruct (μ HEU-02)."""
    adjusted: list[AtomicFact] = []
    for fact in facts:
        if looks_compound(fact):
            note = (fact.reasoning or "").strip()
            suffix = "[compound-heuristic: non-atomic]"
            reasoning = f"{note} {suffix}".strip() if note else suffix
            adjusted.append(fact.model_copy(update={"is_atomic": False, "reasoning": reasoning}))
        else:
            adjusted.append(fact)
    return adjusted
