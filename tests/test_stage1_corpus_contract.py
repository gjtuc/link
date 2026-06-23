"""μ-2b-00 — STAGE-1 corpus contract + memory store (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deconstructor.corpus import (
    CORPUS_SCOPE_BATCH,
    CORPUS_SCOPE_CROSS_RUN,
    InMemoryCorpusStore,
    validate_fact_record,
    validate_run_record,
)
from deconstructor.corpus.contract import facts_from_run_dict

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "design" / "STAGE-1-CORPUS-spec.md"
BRANCH2B = ROOT / "docs" / "design" / "BRANCH-2b-spec.md"
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "stage1_corpus_contract_sample.json"


def test_stage1_corpus_spec_exists():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-2b-00" in body
    assert "cross_run" in body
    assert "InMemoryCorpusStore" in body or "memory_store" in body
    assert "pipeline_batch" in body


def test_stage1_corpus_contract_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-2b-00"
    assert data["scope"] == "cross_run"
    run = validate_run_record(data["run"])
    assert run.merge_mode == CORPUS_SCOPE_CROSS_RUN
    facts = facts_from_run_dict(run.run_id, data["facts"])
    assert len(facts) == run.fact_count


def test_validate_run_record_rejects_invalid_scope():
    base = json.loads(SAMPLE.read_text(encoding="utf-8"))["run"]
    bad = dict(base, merge_mode="global_db")
    with pytest.raises(ValueError, match="invalid corpus scope"):
        validate_run_record(bad)


def test_validate_fact_record_requires_provenance():
    with pytest.raises(ValueError, match="source_file"):
        validate_fact_record(
            {
                "fact_id": "x",
                "subject": "Ni",
                "source_file": "",
                "chunk_id": "",
                "run_id": "r1",
            }
        )


def test_memory_store_append_and_cross_run_query():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    store = InMemoryCorpusStore()
    run = validate_run_record(data["run"])
    facts = facts_from_run_dict(run.run_id, data["facts"])
    store.append_run(run, facts)
    assert store.run_count() == 1
    assert store.fact_count() == 2
    assert store.facts_cross_run()[0].subject == "Ni catalyst"
    assert set(store.distinct_source_files()) == {"s0c_paper.txt", "s0c_memo.txt"}


def test_memory_store_two_runs_cross_run():
    store = InMemoryCorpusStore()
    for i, sf in enumerate(("a.txt", "b.txt"), start=1):
        rid = f"run-{i}"
        store.append_run(
            {
                "run_id": rid,
                "session_id": "s1",
                "merge_mode": CORPUS_SCOPE_CROSS_RUN,
                "source_files": [sf],
                "fact_count": 1,
                "created_at": "2026-06-23T22:00:00+00:00",
            },
            [
                {
                    "fact_id": f"f-{i}",
                    "subject": "topic",
                    "source_file": sf,
                    "chunk_id": f"{sf}#1",
                    "run_id": rid,
                }
            ],
        )
    assert store.run_count() == 2
    assert len(store.facts_cross_run()) == 2
    assert store.distinct_source_files() == ["a.txt", "b.txt"]


def test_batch_corpus_scope_still_valid():
    run = validate_run_record(
        {
            "run_id": "batch-1",
            "session_id": "s0",
            "merge_mode": CORPUS_SCOPE_BATCH,
            "source_files": ["s0b_draft_short.txt"],
            "fact_count": 0,
            "created_at": "2026-06-23T22:00:00+00:00",
        }
    )
    assert run.merge_mode == "batch_corpus"


def test_branch2b_spec_links_stage1_corpus():
    body = BRANCH2B.read_text(encoding="utf-8")
    assert "μ-2b-00" in body
