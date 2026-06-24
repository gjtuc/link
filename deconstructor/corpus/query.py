"""
μ-2b-02-R — cross-run corpus read/query contract.

μ-ID: μ-2b-02-R
선행: μ-2b-01 ingest_hook + memory_store
스펙: docs/design/STAGE-1-CORPUS-spec.md § READ 계약

금지: API/UI, Neo4j, pipeline_batch 변경
"""

from __future__ import annotations

from dataclasses import dataclass

from deconstructor.corpus.contract import CorpusFactRecord, CorpusRunRecord
from deconstructor.corpus.store_protocol import CorpusStore


@dataclass(frozen=True)
class CorpusQuerySummary:
    """Aggregated corpus view for one query scope."""

    run_count: int
    fact_count: int
    source_files: tuple[str, ...]
    session_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "run_count": self.run_count,
            "fact_count": self.fact_count,
            "source_files": list(self.source_files),
            "session_id": self.session_id,
        }


def _normalize_optional_id(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} must be non-empty when provided")
    return text


def query_runs(
    store: CorpusStore,
    *,
    session_id: str | None = None,
) -> list[CorpusRunRecord]:
    """List runs; optional ``session_id`` filter. Empty store → []."""
    runs = store.list_runs()
    sid = _normalize_optional_id(session_id, "session_id")
    if sid is None:
        return runs
    return [r for r in runs if r.session_id == sid]


def query_facts(
    store: CorpusStore,
    *,
    session_id: str | None = None,
    run_id: str | None = None,
    subject_contains: str | None = None,
) -> list[CorpusFactRecord]:
    """
    Filter facts across runs.

    Filters combine with AND. Empty store → [].
    """
    sid = _normalize_optional_id(session_id, "session_id")
    rid = _normalize_optional_id(run_id, "run_id")
    allowed_run_ids: set[str] | None = None
    if sid is not None:
        allowed_run_ids = {r.run_id for r in store.list_runs() if r.session_id == sid}
    facts = store.facts_cross_run()
    if allowed_run_ids is not None:
        facts = [f for f in facts if f.run_id in allowed_run_ids]
    if rid is not None:
        facts = [f for f in facts if f.run_id == rid]
    if subject_contains is not None:
        needle = str(subject_contains).strip().lower()
        if needle:
            facts = [f for f in facts if needle in f.subject.lower()]
    return facts


def summarize_corpus(
    store: CorpusStore,
    *,
    session_id: str | None = None,
) -> CorpusQuerySummary:
    """Summary for optional session scope. Empty store → zeros."""
    runs = query_runs(store, session_id=session_id)
    facts = query_facts(store, session_id=session_id)
    files = sorted({f.source_file for f in facts if f.source_file})
    sid = _normalize_optional_id(session_id, "session_id")
    return CorpusQuerySummary(
        run_count=len(runs),
        fact_count=len(facts),
        source_files=tuple(files),
        session_id=sid,
    )
