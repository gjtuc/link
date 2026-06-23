"""μ-2b-02-R — cross-run corpus query (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deconstructor.corpus.ingest_hook import append_pipeline_to_corpus
from deconstructor.corpus.memory_store import InMemoryCorpusStore
from deconstructor.corpus.query import (
    CorpusQuerySummary,
    query_facts,
    query_runs,
    summarize_corpus,
)
from deconstructor.models import AtomicFact

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "stage1_corpus_query_sample.json"


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
    return {"ok": True, "pipeline_states": states}


def _seed_two_runs(store: InMemoryCorpusStore, session_id: str = "sess-demo") -> None:
    append_pipeline_to_corpus(
        store,
        _ok_result([_mock_state("a.txt", "Ni catalyst", "f-a")]),
        session_id=session_id,
        run_id="run-1",
    )
    append_pipeline_to_corpus(
        store,
        _ok_result([_mock_state("b.txt", "CH4 conversion", "f-b")]),
        session_id=session_id,
        run_id="run-2",
    )


def test_corpus_query_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-2b-02-R"
    assert data["expected"]["query_facts_session"]["fact_count"] == 2
    assert "empty_store_summary" in data["expected"]


def test_empty_store_returns_zero_summary():
    store = InMemoryCorpusStore()
    summary = summarize_corpus(store)
    assert summary == CorpusQuerySummary(
        run_count=0,
        fact_count=0,
        source_files=(),
        session_id=None,
    )
    assert query_runs(store) == []
    assert query_facts(store) == []


def test_two_runs_session_query_accumulates():
    store = InMemoryCorpusStore()
    _seed_two_runs(store)
    runs = query_runs(store, session_id="sess-demo")
    assert len(runs) == 2
    assert [r.run_id for r in runs] == ["run-1", "run-2"]
    facts = query_facts(store, session_id="sess-demo")
    assert len(facts) == 2
    assert {f.fact_id for f in facts} == {"f-a", "f-b"}


def test_query_facts_run_id_filter():
    store = InMemoryCorpusStore()
    _seed_two_runs(store)
    facts = query_facts(store, session_id="sess-demo", run_id="run-1")
    assert len(facts) == 1
    assert facts[0].fact_id == "f-a"


def test_query_facts_subject_contains_filter():
    store = InMemoryCorpusStore()
    _seed_two_runs(store)
    facts = query_facts(store, session_id="sess-demo", subject_contains="CH4")
    assert len(facts) == 1
    assert facts[0].fact_id == "f-b"


def test_summarize_corpus_matches_sample_expectations():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    store = InMemoryCorpusStore()
    _seed_two_runs(store, session_id=data["session_id"])
    summary = summarize_corpus(store, session_id=data["session_id"])
    assert summary.run_count == 2
    assert summary.fact_count == 2
    assert set(summary.source_files) == {"a.txt", "b.txt"}
    assert summary.session_id == data["session_id"]


def test_query_rejects_empty_session_id():
    store = InMemoryCorpusStore()
    with pytest.raises(ValueError, match="session_id"):
        query_runs(store, session_id="  ")


def test_wrong_session_returns_empty():
    store = InMemoryCorpusStore()
    _seed_two_runs(store)
    assert query_runs(store, session_id="other") == []
    assert query_facts(store, session_id="other") == []
