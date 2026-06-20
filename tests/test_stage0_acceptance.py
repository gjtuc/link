"""
STAGE 0-3 — Acceptance criteria (documented tests).

See ``docs/design/STAGE-0-3-acceptance-criteria.md`` for AC-* definitions.

These tests are **fast, offline** where possible. LLM/pipeline E2E belongs in
separate expensive suite (AC-DEC-02 — SHOULD, not MUST gate).

STAGE 0-5: P0 MUST gate — see ``docs/design/STAGE-0-5-implementation-roadmap.md``
(Sprint 0~4; T-FAST every sprint).
"""

from __future__ import annotations

import pytest

from deconstructor.web.document_chunks import chunk_text
from deconstructor.web.extract import (
    document_sources_from_bytes,
    expand_document_sources,
)


@pytest.fixture(autouse=True)
def _document_ingest_mode(monkeypatch):
    monkeypatch.setenv("LINK_DOCUMENT_INGEST", "document")
    import deconstructor.web.extract as ex

    monkeypatch.setattr(ex, "DOCUMENT_INGEST_MODE", "document")
    monkeypatch.setattr(ex, "_use_document_deconstruct_ingest", lambda: True)


# --- AC-ING-* ---


def test_ac_ing_03_long_text_multiple_chunks():
    """AC-ING-03: >8k chars → ≥2 chunks."""
    text = ("paragraph. " * 2000).strip()
    chunks = chunk_text(text, max_chars=8000, overlap=0)
    assert len(chunks) >= 2


def test_ac_ing_04_chunk_labels(tmp_path):
    """AC-ING-04: labels contain chunk index."""
    long_text = ("Ni loading increased. " * 500).strip()
    path = tmp_path / "paper.txt"
    path.write_text(long_text, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    assert len(sources) >= 2
    assert any("청크" in s.label for s in sources)


def test_ac_neg_02_long_text_not_summarized_to_few_sentences(tmp_path):
    """AC-NEG-02 / F0-B1: document mode preserves bulk text."""
    long_text = ("claim with evidence. " * 800).strip()
    path = tmp_path / "draft.txt"
    path.write_text(long_text, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    joined = " ".join(s.text for s in sources)
    assert len(joined) > 2000
    assert joined.count(".") > 10


def test_ac_ing_01_char_retention_ratio(tmp_path):
    """AC-ING-01: sum(chunk chars) / raw ≥ 0.95 (plain text proxy)."""
    raw = ("x" * 20_000) + "\n\n" + ("y" * 20_000)
    path = tmp_path / "big.txt"
    path.write_text(raw, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    ratio = sum(len(s.text) for s in sources) / len(raw.strip())
    assert ratio >= 0.95


# --- AC-NEG-* ---


def test_ac_neg_01_document_mode_does_not_use_maybe_summarize_on_expand():
    """AC-NEG-01 / F0-A2: expand_document_sources returns raw chunks, not 2-5 sentences."""
    raw = ("Experimental result: CH4 conversion increased. " * 300).strip()
    sources = expand_document_sources("paper.pdf", raw, kind="document")
    assert len(sources) >= 2
    assert sum(len(s.text) for s in sources) > 1000
