"""
Dreamer Flash breadth diversity metrics (μ-DR-DIV).

Pure functions — no LLM. Used by dreamer_breadth_probe.py and pytest stubs.
"""

from __future__ import annotations

import re
from typing import Protocol


class _HypothesisLike(Protocol):
    subject: str
    mechanism: str


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def mechanism_similarity(a: str, b: str) -> float:
    """Jaccard similarity on mechanism token sets."""
    ta, tb = _token_set(a), _token_set(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def exact_duplicate_rate(hypotheses: list[_HypothesisLike]) -> float:
    """Share of rows that duplicate another (subject + mechanism, normalized)."""
    if not hypotheses:
        return 0.0
    keys = [(_norm(h.subject), _norm(h.mechanism)) for h in hypotheses]
    unique = len(set(keys))
    return 1.0 - unique / len(keys)


def unique_subject_ratio(hypotheses: list[_HypothesisLike]) -> float:
    """Distinct subjects / row count."""
    if not hypotheses:
        return 0.0
    subjects = {_norm(h.subject) for h in hypotheses}
    return len(subjects) / len(hypotheses)


def mechanism_similarity_mean(hypotheses: list[_HypothesisLike]) -> float:
    """Mean pairwise Jaccard similarity across mechanism texts."""
    n = len(hypotheses)
    if n < 2:
        return 0.0
    total = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += mechanism_similarity(hypotheses[i].mechanism, hypotheses[j].mechanism)
            pairs += 1
    return total / pairs


def diversity_metrics(hypotheses: list[_HypothesisLike]) -> dict[str, float]:
    return {
        "exact_duplicate_rate": exact_duplicate_rate(hypotheses),
        "unique_subject_ratio": unique_subject_ratio(hypotheses),
        "mechanism_similarity_mean": mechanism_similarity_mean(hypotheses),
        "count": float(len(hypotheses)),
    }
