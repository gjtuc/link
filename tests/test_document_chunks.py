"""document_chunks — Deconstruct용 청크 분할."""

from deconstructor.web.document_chunks import chunk_pdf_page_texts, chunk_text

__all__ = ["chunk_text", "chunk_pdf_page_texts"]


def test_chunk_text_short_unchanged():
    assert chunk_text("hello world") == ["hello world"]


def test_chunk_text_splits_on_paragraphs():
    para = "word " * 500
    text = f"{para.strip()}\n\n{para.strip()}\n\n{para.strip()}"
    chunks = chunk_text(text, max_chars=1200, overlap=0)
    assert len(chunks) >= 2
    assert all(len(c) <= 1200 for c in chunks)


def test_chunk_pdf_pages_labels():
    pages = ["page one " * 100, "page two " * 100, "page three " * 100]
    chunks = chunk_pdf_page_texts(pages, max_chars=500)
    assert len(chunks) >= 2
    labels = [c[0] for c in chunks]
    assert any(lbl.startswith("p.") for lbl in labels)


def test_document_sources_no_summarize(monkeypatch, tmp_path):
    from deconstructor.web.extract import document_sources_from_bytes

    monkeypatch.setenv("LINK_DOCUMENT_INGEST", "document")
    # re-import mode flag
    import deconstructor.web.extract as ex

    monkeypatch.setattr(ex, "DOCUMENT_INGEST_MODE", "document")
    monkeypatch.setattr(ex, "_use_document_deconstruct_ingest", lambda: True)

    long_text = ("Ni loading increased. " * 400).strip()
    path = tmp_path / "paper.txt"
    path.write_text(long_text, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    assert len(sources) >= 2
    joined = " ".join(s.text for s in sources)
    assert "Ni loading increased" in joined
    assert len(joined) > 2000
