"""μ-2b-02-API — GET /api/status cross_run_corpus block (offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from deconstructor.corpus.ingest_hook import append_pipeline_to_corpus, reset_corpus_store
from deconstructor.corpus.status_block import build_corpus_status_block
from deconstructor.models import AtomicFact

ROOT = Path(__file__).resolve().parents[1]
SERVER_PY = ROOT / "deconstructor" / "web" / "server.py"


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
def _fresh_store():
    reset_corpus_store()
    yield
    reset_corpus_store()


def test_status_block_disabled_when_env_off(monkeypatch):
    monkeypatch.delenv("LINK_CROSS_RUN_CORPUS", raising=False)
    block = build_corpus_status_block()
    assert block["enabled"] is False
    assert block["run_count"] == 0
    assert block["fact_count"] == 0
    assert block["source_files"] == []
    assert block["session_id"] is None


def test_status_block_reflects_store_when_enabled(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    store = reset_corpus_store()
    append_pipeline_to_corpus(
        store,
        {"ok": True, "pipeline_states": [_mock_state("a.txt", "Ni catalyst", "f-a")]},
        session_id="sess-api",
        run_id="run-api-1",
    )
    block = build_corpus_status_block(session_id="sess-api")
    assert block["enabled"] is True
    assert block["run_count"] == 1
    assert block["fact_count"] == 1
    assert block["source_files"] == ["a.txt"]
    assert block["session_id"] == "sess-api"


def test_status_block_uses_link_session_id_env(monkeypatch):
    monkeypatch.setenv("LINK_CROSS_RUN_CORPUS", "1")
    monkeypatch.setenv("LINK_SESSION_ID", "env-sess")
    store = reset_corpus_store()
    append_pipeline_to_corpus(
        store,
        {"ok": True, "pipeline_states": [_mock_state("b.txt", "CH4", "f-b")]},
        session_id="env-sess",
        run_id="run-env",
    )
    append_pipeline_to_corpus(
        store,
        {"ok": True, "pipeline_states": [_mock_state("c.txt", "other", "f-c")]},
        session_id="other-sess",
        run_id="run-other",
    )
    block = build_corpus_status_block()
    assert block["enabled"] is True
    assert block["run_count"] == 1
    assert block["fact_count"] == 1
    assert block["session_id"] == "env-sess"


def test_server_wires_cross_run_corpus_on_api_status():
    source = SERVER_PY.read_text(encoding="utf-8")
    assert 'path == "/api/status"' in source
    assert '"cross_run_corpus"' in source
    assert "build_corpus_status_block" in source
