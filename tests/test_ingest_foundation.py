"""
INGEST Foundation — Phase R (읽기 확인) tests.

See ``docs/design/INGEST-FOUNDATION-spec.md`` (μ-R-*).
"""

from __future__ import annotations

import pytest

from deconstructor.web.extract import (
    document_sources_from_bytes,
    expand_document_sources,
    from_text,
)
from deconstructor.web.ingest_verify import (
    CHAR_RETENTION_MIN,
    verify_read,
)


@pytest.fixture(autouse=True)
def _document_mode(monkeypatch):
    monkeypatch.setenv("LINK_DOCUMENT_INGEST", "document")
    import deconstructor.web.extract as ex

    monkeypatch.setattr(ex, "DOCUMENT_INGEST_MODE", "document")
    monkeypatch.setattr(ex, "_use_document_deconstruct_ingest", lambda: True)


def test_mu_r_mode_01_document_mode():
    sources = expand_document_sources("t.txt", "hello " * 50, kind="text", source_file="t.txt")
    report = verify_read(sources)
    assert any(c.id == "μ-R-MODE-01" and c.ok for c in report.checks)


def test_mu_r_ext_01_nonempty(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("content here", encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    report = verify_read(sources, raw_by_file={path.name: path.read_text(encoding="utf-8")})
    assert report.ok
    assert report.blocking is False


def test_mu_r_ret_01_char_retention(tmp_path):
    raw = ("paragraph one. " * 400).strip()
    path = tmp_path / "big.txt"
    path.write_text(raw, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    report = verify_read(sources, raw_by_file={path.name: raw})
    ret_checks = [c for c in report.checks if c.id == "μ-R-RET-01"]
    assert ret_checks and all(c.ok for c in ret_checks)
    got = sum(len(s.text) for s in sources)
    assert got / len(raw) >= CHAR_RETENTION_MIN


def test_mu_r_chk_01_long_multi_chunk(tmp_path):
    raw = ("Ni loading increased. " * 500).strip()
    path = tmp_path / "long.txt"
    path.write_text(raw, encoding="utf-8")
    sources = document_sources_from_bytes(path.read_bytes(), path.name, "text/plain")
    assert len(sources) >= 2
    report = verify_read(sources, raw_by_file={path.name: raw})
    chk = [c for c in report.checks if c.id.startswith("μ-R-CHK-01:")]
    assert chk and all(c.ok for c in chk)


def test_mu_r_chk_04_short_single_chunk():
    short = from_text("Executive summary only. " * 20)
    sources = expand_document_sources("draft.txt", short, kind="text", source_file="draft.txt")
    assert len(sources) == 1
    report = verify_read(sources)
    chk4 = [c for c in report.checks if c.id.startswith("μ-R-CHK-04:")]
    assert chk4 and all(c.ok for c in chk4)


def test_mu_r_meta_01_source_file():
    sources = expand_document_sources("f.txt", "text " * 100, kind="text", source_file="f.txt")
    report = verify_read(sources)
    meta = [c for c in report.checks if c.id.startswith("μ-R-META-01:")]
    assert meta and all(c.ok for c in meta)


def test_mu_r_bat_01_multi_file():
    s1 = expand_document_sources("a.txt", "file a " * 50, kind="text", source_file="a.txt")
    s2 = expand_document_sources("b.txt", "file b " * 50, kind="text", source_file="b.txt")
    report = verify_read(s1 + s2)
    bat = [c for c in report.checks if c.id == "μ-R-BAT-01"]
    assert bat and bat[0].ok


def test_mu_r_guard_01_f0_a2_blocks():
    from deconstructor.web.extract import ExtractedSource

    bad = [
        ExtractedSource(
            kind="document",
            label="paper.pdf (p.1-4)",
            text="tiny",
            source_file="paper.pdf",
            chunk_id="paper.pdf#chunk-1/1",
            chunk_index=1,
            chunk_total=1,
            document_page_count=10,
        )
    ]
    report = verify_read(bad)
    assert report.blocking is True
    guard = [c for c in report.checks if c.id == "μ-R-GUARD-01"]
    assert guard and not guard[0].ok
    assert not report.ok


def test_read_verify_report_to_dict():
    sources = expand_document_sources("x.txt", "ok " * 30, kind="text", source_file="x.txt")
    d = verify_read(sources).to_dict()
    assert "checks" in d and "passed" in d and "ok" in d


def test_s0b_fixtures_read_phase():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    short = root / "tests" / "fixtures" / "s0b_draft_short.txt"
    long = root / "tests" / "fixtures" / "s0b_draft_long.txt"
    if not short.is_file():
        pytest.skip("run scripts/generate_s0bc_fixtures.py")
    short_src = expand_document_sources(
        "short",
        from_text(short.read_text(encoding="utf-8")),
        kind="text",
        source_file=short.name,
    )
    long_src = expand_document_sources(
        "long",
        from_text(long.read_text(encoding="utf-8")),
        kind="text",
        source_file=long.name,
    )
    report = verify_read(
        short_src + long_src,
        raw_by_file={
            short.name: short.read_text(encoding="utf-8"),
            long.name: long.read_text(encoding="utf-8"),
        },
    )
    must_fail = [c for c in report.checks if c.severity == "must" and not c.ok]
    assert not must_fail, must_fail
    assert report.ok
