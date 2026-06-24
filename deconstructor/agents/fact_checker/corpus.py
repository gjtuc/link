"""
Sprint 5 (G-FC-CORPUS) — document-internal Fact-Checker.

Verifies Dreamer hypotheses against extracted ``completed_facts`` corpus pool
instead of Tavily when ``mode=corpus``.

See ``docs/design/SPRINT-5-corpus-fc-spec.md``.
"""

from __future__ import annotations

import logging

from deconstructor.agents.fact_checker.schemas import VerificationVerdict
from deconstructor.models import AtomicFact
from deconstructor.web.corpus_bridge import normalize_subject

logger = logging.getLogger(__name__)

TOKEN_OVERLAP_MIN = 0.5


def _log(msg: str) -> None:
    line = f"[CHECK-S5-corpus] {msg}"
    logger.info(line)
    print(line)


def collect_corpus_pool(state: dict) -> list[AtomicFact]:
    """
    Merge batch ``corpus_fact_pool`` with in-run ``completed_facts`` (POOL-01, POOL-03).

    Only extracted atomic facts — inferred/promoted excluded from evidence pool.
    """
    seen: set[str] = set()
    pool: list[AtomicFact] = []
    for fact in (state.get("corpus_fact_pool") or []) + (state.get("completed_facts") or []):
        if not isinstance(fact, AtomicFact):
            continue
        if fact.id in seen:
            continue
        seen.add(fact.id)
        if fact.source_type != "extracted":
            continue
        if not fact.is_atomic:
            continue
        if not (fact.subject or "").strip():
            continue
        pool.append(fact)
    return pool


def _token_overlap(a: str, b: str) -> float:
    ta = {t for t in a.split() if len(t) > 2}
    tb = {t for t in b.split() if len(t) > 2}
    if not ta:
        return 0.0
    return len(ta & tb) / len(ta)


def _state_shares_signal(a: str, b: str) -> bool:
    """Lightweight state_change overlap — avoid promote on subject alone."""
    aa = (a or "").lower()
    bb = (b or "").lower()
    if not aa or not bb:
        return True
    ta = {t for t in aa.replace("->", " ").split() if len(t) > 3}
    tb = {t for t in bb.replace("->", " ").split() if len(t) > 3}
    if not ta or not tb:
        return aa[:20] == bb[:20]
    return bool(ta & tb)


def _subject_match_level(hyp: AtomicFact, ref: AtomicFact) -> str | None:
    h = normalize_subject(hyp.subject)
    r = normalize_subject(ref.subject)
    if not h or not r:
        return None
    if h == r:
        return "exact"
    if h in r or r in h:
        return "substring"
    if _token_overlap(h, r) >= TOKEN_OVERLAP_MIN:
        return "token"
    return None


def corpus_verify_hypothesis(
    fact: AtomicFact,
    pool: list[AtomicFact],
) -> VerificationVerdict:
    """
    Rule-based corpus verification (MAT-01~04).

    Promote when subject/anchor evidence exists in document pool; else drop.
    """
    if not pool:
        _log(f"DROP empty pool subject={fact.subject!r}")
        return VerificationVerdict(
            accepted=False,
            reason="corpus: no extracted facts in document pool to verify hypothesis",
        )

    if fact.anchor_fact_id:
        for ref in pool:
            if ref.id == fact.anchor_fact_id:
                _log(f"PROMOTE anchor match id={ref.id[:8]}.. subject={fact.subject!r}")
                return VerificationVerdict(
                    accepted=True,
                    reason=f"corpus: anchor fact {ref.subject!r} present in document",
                )

    for ref in pool:
        if ref.id == fact.id:
            continue
        level = _subject_match_level(fact, ref)
        if level == "exact":
            _log(f"PROMOTE exact subject={fact.subject!r} ref={ref.subject!r}")
            return VerificationVerdict(
                accepted=True,
                reason=f"corpus: exact subject match with extracted fact {ref.subject!r}",
            )
        if level == "substring":
            _log(f"PROMOTE substring subject={fact.subject!r} ref={ref.subject!r}")
            return VerificationVerdict(
                accepted=True,
                reason=f"corpus: subject overlap with extracted fact {ref.subject!r}",
            )
        if level == "token" and _state_shares_signal(fact.state_change, ref.state_change):
            _log(f"PROMOTE token+state subject={fact.subject!r} ref={ref.subject!r}")
            return VerificationVerdict(
                accepted=True,
                reason=(
                    f"corpus: subject token overlap + state signal with {ref.subject!r}"
                ),
            )

    _log(f"DROP no corpus evidence subject={fact.subject!r}")
    return VerificationVerdict(
        accepted=False,
        reason="corpus: no supporting extracted fact for hypothesis subject/mechanism",
    )
