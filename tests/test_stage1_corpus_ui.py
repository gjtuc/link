"""μ-2b-02-UI — cross-run corpus status hint in index.html (offline wiring)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "web" / "index.html"


def test_stage1_index_html_wires_cross_run_corpus_hint():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="corpus-hint"' in html
    assert "corpus-hint" in html
    assert "cross_run_corpus" in html
    assert "formatCrossRunCorpusLine" in html
    assert "updateCrossRunCorpusHint" in html
    assert "updateBackendStatus" in html
    assert "분석 기록 모음:" in html
    assert "아직 분석한 적 없음" in html
    assert "출처 파일" in html
    assert "updateCrossRunCorpusHint(cachedBackendStatus.cross_run_corpus" in html
    assert "refreshBackendStatusFromApi" in html
    assert "await refreshBackendStatusFromApi()" in html
