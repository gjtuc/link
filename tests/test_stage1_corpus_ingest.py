"""μ-2b-01 — cross-run corpus ingest hook (offline)."""

from __future__ import annotations

import os

import pytest

from deconstructor.corpus.ingest_hook import (
    append_pipeline_to_corpus,
    cross_run_corpus_enabled,
    maybe_append_batch_corpus,
    reset_corpus_store,
)
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


def _ok_result(states: list[dict]) -> dict:
    return {"ok": True, "pipeline_states": states, "atomic_facts_total": len(states)}


@pytest.fixture(autouse=True)
def _fresh_store():
    reset_corpus_store()
    yield
    reset_corpus_store()


def test_cross_run_env_default_off():
    os.environ.pop("LINK_CROSS_RUN_CORPUS", None)
    assert cross_run_corpus_enabled() is False


def test_two_runs_accumulate_in_store(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    store = reset_corpus_store()
    states1 = [_mock_state("a.txt", "Ni catalyst", "f-a")]
    states2 = [_mock_state("b.txt", "CH4 conversion", "f-b")]
    assert append_pipeline_to_corpus(store, _ok_result(states1), session_id="sess-1", run_id="run-1")
    assert append_pipeline_to_corpus(store, _ok_result(states2), session_id="sess-1", run_id="run-2")
    assert store.run_count() == 2
    assert store.fact_count() == 2
    cross = store.facts_cross_run()
    assert {f.fact_id for f in cross} == {"f-a", "f-b"}
    assert store.distinct_source_files() == ["a.txt", "b.txt"]


def test_env_off_maybe_append_leaves_store_empty(monkeypatch):
    monkeypatch.delenv("LINK_CROSS_RUN_CORPUS", raising=False)
    store = reset_corpus_store()
    states = [_mock_state("a.txt", "Ni", "f-1")]
    maybe_append_batch_corpus(_ok_result(states), states, run_id="run-x", session_id="s")
    assert store.run_count() == 0
    assert store.fact_count() == 0


def test_env_on_maybe_append_records_run(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    store = reset_corpus_store()
    states = [_mock_state("memo.txt", "topic", "f-m")]
    maybe_append_batch_corpus(_ok_result(states), states, run_id="run-y", session_id="sess-y")
    assert store.run_count() == 1
    assert store.facts_for_run("run-y")[0].subject == "topic"


def test_failed_pipeline_not_appended():
    store = reset_corpus_store()
    states = [_mock_state("a.txt", "Ni", "f-1")]
    assert (
        append_pipeline_to_corpus(
            store,
            {"ok": False, "pipeline_states": states},
            session_id="s",
            run_id="r",
        )
        is False
    )
    assert store.run_count() == 0


def test_hook_failure_does_not_mutate_pipeline_result(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    result = {"ok": True, "items_processed": 1}
    states = [{"source_document_meta": {}, "completed_facts": []}]
    before = dict(result)
    maybe_append_batch_corpus(result, states, run_id="run-z", session_id="s")
    assert result == before
