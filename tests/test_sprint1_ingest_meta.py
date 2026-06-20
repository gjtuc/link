"""
Sprint 1 — ingest provenance (SP1-TEST-01, AC-ING-05).

See ``docs/design/SPRINT-1-ingest-meta-spec.md``.
"""

from __future__ import annotations

import pytest

from deconstructor.models import AtomicFact
from deconstructor.provenance.assign import tag_as_extracted
from deconstructor.provenance.source_meta import make_chunk_id, page_range_from_suffix
from deconstructor.web.extract import document_sources_from_bytes, expand_document_sources


@pytest.fixture(autouse=True)
def _document_ingest_mode(monkeypatch):
    monkeypatch.setenv("LINK_DOCUMENT_INGEST", "document")
    import deconstructor.web.extract as ex

    monkeypatch.setattr(ex, "DOCUMENT_INGEST_MODE", "document")
    monkeypatch.setattr(ex, "_use_document_deconstruct_ingest", lambda: True)


def test_sp1_p03_make_chunk_id():
    assert make_chunk_id("paper.pdf", 2, 5) == "paper.pdf#chunk-2/5"
    assert make_chunk_id("a#b/c", 1, 1) == "a_b_c#chunk-1/1"


def test_sp1_p03_page_range_from_suffix():
    assert page_range_from_suffix("p.1-3") == "p.1-3"
    assert page_range_from_suffix("") == ""
    assert page_range_from_suffix("청크") == ""


def test_sp1_i01_expand_document_sources_multi_chunk():
    long_text = ("Experimental result. " * 500).strip()
    sources = expand_document_sources("draft.txt", long_text, source_file="draft.txt")
    assert len(sources) >= 2
    ids = {s.chunk_id for s in sources}
    assert len(ids) == len(sources)
    assert all(s.source_file == "draft.txt" for s in sources)
    assert all(s.chunk_id.endswith(f"/{s.chunk_total}") for s in sources)


def test_sp1_i03_document_sources_from_bytes(tmp_path):
    long_text = ("Ni loading increased. " * 400).strip()
    path = tmp_path / "paper.txt"
    path.write_text(long_text, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    assert len(sources) >= 2
    assert sources[0].source_file == "paper.txt"
    assert sources[0].chunk_id == make_chunk_id("paper.txt", 1, len(sources))


def test_sp1_l04_tag_as_extracted_stamps_document_meta():
    fact = AtomicFact(subject="Ni catalyst", state_change="loading -> increased", is_atomic=True)
    meta = {
        "source_file": "paper.pdf",
        "page_range": "p.2-4",
        "chunk_id": "paper.pdf#chunk-2/3",
    }
    tagged = tag_as_extracted([fact], document_meta=meta)
    assert len(tagged) == 1
    assert tagged[0].source_file == "paper.pdf"
    assert tagged[0].page_range == "p.2-4"
    assert tagged[0].chunk_id == "paper.pdf#chunk-2/3"


def test_sp1_pipeline_dry_run_carries_meta():
    from deconstructor.web.link_steps import LinkStepTracker
    from deconstructor.web.pipeline_link import run_pipeline_with_steps

    meta = {
        "source_file": "chunk.txt",
        "chunk_id": "chunk.txt#chunk-1/2",
        "chunk_index": 1,
        "chunk_total": 2,
    }
    state = run_pipeline_with_steps(
        LinkStepTracker(),
        1,
        "Grid power went off at 10:00.",
        dry_run=True,
        enable_dreamer=False,
        fact_checker_dry_run=True,
        source_document_meta=meta,
    )
    assert state.get("source_document_meta") == meta
    completed = state.get("completed_facts") or []
    assert completed, "dry_run should produce completed facts"
    assert all(f.chunk_id == meta["chunk_id"] for f in completed)
    assert all(f.source_file == meta["source_file"] for f in completed)
