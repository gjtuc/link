"""μ-Q2-04 — pre-upload capability warning UI (offline string assert)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "web" / "index.html"


def test_index_html_capability_warning_wired():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "/api/capabilities" in html
    assert "cap-warn-modal" in html
    assert "ensureCapabilityAck" in html
    assert "그래도 실행" in html
    assert "나중에" in html
    assert "미검증" in html
    assert "미지원" in html
    assert "확인됨" in html


def test_capability_status_labels():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "formatCapabilityStatus" in html
    assert 'status === "verified"' in html or "verified" in html
