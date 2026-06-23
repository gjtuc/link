"""μ-2b-03-00 — CorpusStore factory + memory adapter (offline)."""

from __future__ import annotations

import os

import pytest

from deconstructor.corpus.factory import (
    clear_corpus_store_singleton,
    corpus_backend,
    get_corpus_store,
    reset_corpus_store,
)
from deconstructor.corpus.ingest_hook import append_pipeline_to_corpus, maybe_append_batch_corpus
from deconstructor.corpus.memory_adapter import MemoryCorpusStoreAdapter
from deconstructor.corpus.memory_store import InMemoryCorpusStore
from deconstructor.corpus.query import query_facts, summarize_corpus
from deconstructor.corpus.status_block import build_corpus_status_block
from deconstructor.models import AtomicFact


def _mock_state(source_file: str, subject: str, fact_id: str) -> dict:
    return {
        "source_document_meta": {"source_file": source_file},
        "completed_facts": [
            AtomicFact(
                id=fact_id,
                subject=subject,
                state_change="a -> b",
                source_file=source_file,
                chunk_id=f"{source_file}#chunk-1/1",
            )
        ],
    }


@pytest.fixture(autouse=True)
def _fresh_store(monkeypatch):
    monkeypatch.delenv("LINK_CORPUS_BACKEND", raising=False)
    reset_corpus_store()
    yield
    reset_corpus_store()


def test_default_backend_is_memory():
    assert corpus_backend() == "memory"


def test_get_corpus_store_returns_memory_adapter():
    store = get_corpus_store()
    assert isinstance(store, MemoryCorpusStoreAdapter)


def test_neo4j_backend_not_implemented(monkeypatch):
    monkeypatch.setenv("LINK_CORPUS_BACKEND", "neo4j")
    clear_corpus_store_singleton()
    with pytest.raises(NotImplementedError, match="μ-2b-03-01"):
        get_corpus_store()


def test_factory_path_matches_direct_ingest_query_status(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    store = reset_corpus_store()
    append_pipeline_to_corpus(
        store,
        {"ok": True, "pipeline_states": [_mock_state("a.txt", "Ni catalyst", "f-a")]},
        session_id="sess-factory",
        run_id="run-f1",
    )
    append_pipeline_to_corpus(
        store,
        {"ok": True, "pipeline_states": [_mock_state("b.txt", "CH4", "f-b")]},
        session_id="sess-factory",
        run_id="run-f2",
    )
    assert store.run_count() == 2
    facts = query_facts(store, session_id="sess-factory")
    assert len(facts) == 2
    block = build_corpus_status_block(session_id="sess-factory")
    assert block["enabled"] is True
    assert block["run_count"] == 2
    assert block["fact_count"] == 2


def test_maybe_append_uses_factory_singleton(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    reset_corpus_store()
    states = [_mock_state("x.txt", "topic", "f-x")]
    maybe_append_batch_corpus(
        {"ok": True, "pipeline_states": states},
        states,
        run_id="run-singleton",
        session_id="sess-s",
    )
    assert get_corpus_store().run_count() == 1


def test_reset_wraps_raw_in_memory_store():
    inner = InMemoryCorpusStore()
    wrapped = reset_corpus_store(inner)
    assert isinstance(wrapped, MemoryCorpusStoreAdapter)
    assert wrapped.inner is inner


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("LINK_CORPUS_BACKEND", "invalid")
    clear_corpus_store_singleton()
    with pytest.raises(ValueError, match="unknown LINK_CORPUS_BACKEND"):
        get_corpus_store()
