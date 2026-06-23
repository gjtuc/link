"""
μ-2b-01 — cross-run corpus ingest hook (read-only side-effect).

μ-ID: μ-2b-01
선행: μ-2b-00 contract + memory_store
실행: LINK_CROSS_RUN_CORPUS=1 시 pipeline_batch 성공 후 append
스펙: docs/design/STAGE-1-CORPUS-spec.md § μ-2b-01

금지: pipeline 실패 시 결과 변경, Neo4j, live E2E
"""

from __future__ import annotations

import os
from typing import Any

from deconstructor.corpus.contract import (
    CORPUS_SCOPE_CROSS_RUN,
    CorpusFactRecord,
    CorpusRunRecord,
    utc_now_iso,
)
from deconstructor.corpus.memory_store import InMemoryCorpusStore

_ENV_CROSS_RUN = "LINK_CROSS_RUN_CORPUS"
_ENV_SESSION_ID = "LINK_SESSION_ID"

_global_store: InMemoryCorpusStore | None = None


def cross_run_corpus_enabled() -> bool:
    return os.getenv(_ENV_CROSS_RUN, "").strip().lower() in ("1", "true", "yes")


def get_corpus_store() -> InMemoryCorpusStore:
    global _global_store
    if _global_store is None:
        _global_store = InMemoryCorpusStore()
    return _global_store


def reset_corpus_store(store: InMemoryCorpusStore | None = None) -> InMemoryCorpusStore:
    """Tests: replace process singleton."""
    global _global_store
    _global_store = store if store is not None else InMemoryCorpusStore()
    return _global_store


def _source_file_for_fact(fact: Any, meta: dict[str, Any]) -> str:
    sf = getattr(fact, "source_file", None) or meta.get("source_file") or ""
    return str(sf).strip()


def facts_from_pipeline_states(
    pipeline_states: list[dict[str, Any]],
    run_id: str,
) -> tuple[list[str], list[CorpusFactRecord]]:
    """Extract CorpusFactRecord list + distinct source_files from pipeline states."""
    source_files: set[str] = set()
    facts: list[CorpusFactRecord] = []
    for state in pipeline_states:
        meta = dict(state.get("source_document_meta") or {})
        meta_sf = str(meta.get("source_file") or "").strip()
        if meta_sf:
            source_files.add(meta_sf)
        for fact in state.get("completed_facts") or []:
            subject = str(getattr(fact, "subject", "") or "").strip()
            if not subject:
                continue
            source_file = _source_file_for_fact(fact, meta)
            if not source_file:
                continue
            source_files.add(source_file)
            facts.append(
                CorpusFactRecord(
                    fact_id=str(getattr(fact, "id", "") or ""),
                    subject=subject,
                    source_file=source_file,
                    run_id=run_id,
                    chunk_id=str(getattr(fact, "chunk_id", "") or ""),
                )
            )
    if not source_files and facts:
        source_files = {f.source_file for f in facts}
    return sorted(source_files), facts


def append_pipeline_to_corpus(
    store: InMemoryCorpusStore,
    pipeline_result: dict[str, Any],
    *,
    session_id: str,
    run_id: str,
) -> bool:
    """
    Append one cross-run corpus record. Returns True if appended.

    Does not mutate ``pipeline_result``. Raises on validation errors (caller may catch).
    """
    if not pipeline_result.get("ok"):
        return False
    states = pipeline_result.get("pipeline_states") or []
    if not states:
        return False
    source_files, facts = facts_from_pipeline_states(states, run_id)
    if not source_files:
        return False
    run = CorpusRunRecord(
        run_id=run_id,
        session_id=session_id,
        merge_mode=CORPUS_SCOPE_CROSS_RUN,
        source_files=tuple(source_files),
        fact_count=len(facts),
        created_at=utc_now_iso(),
    )
    store.append_run(run, facts)
    return True


def maybe_append_batch_corpus(
    pipeline_result: dict[str, Any],
    pipeline_states: list[dict[str, Any]],
    *,
    run_id: str,
    session_id: str | None = None,
) -> None:
    """Env-gated hook from pipeline_batch — failures are swallowed."""
    if not cross_run_corpus_enabled():
        return
    if not pipeline_result.get("ok"):
        return
    sid = (session_id or os.getenv(_ENV_SESSION_ID) or run_id).strip()
    try:
        payload = {**pipeline_result, "pipeline_states": pipeline_states}
        append_pipeline_to_corpus(get_corpus_store(), payload, session_id=sid, run_id=run_id)
    except Exception:
        return
