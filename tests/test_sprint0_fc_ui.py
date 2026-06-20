"""
Sprint 0 — Fact-Checker stub UI (SP0-TEST-01).

See ``docs/design/STAGE-0-5-implementation-roadmap.md`` Appendix A.
AC-FC-01 (status JSON), AC-FC-02 (UI wiring).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deconstructor import config

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "web" / "index.html"


@pytest.fixture
def _reload_config(monkeypatch):
    """Isolate TAVILY_* for mode tests."""
    monkeypatch.setattr(config, "TAVILY_API_KEY", "test-key", raising=False)
    yield


def test_sp0_fc_mode_stub_when_tavily_disabled(_reload_config, monkeypatch):
    """AC-FC-01/02: TAVILY_DISABLED + corpus off → fact_checker stub."""
    monkeypatch.setattr(config, "TAVILY_DISABLED", True)
    monkeypatch.setattr(config, "CORPUS_FC_ENABLED", False)
    assert config.tavily_enabled() is False
    assert config.fact_checker_status_mode() == "stub"


def test_sp0_fc_mode_corpus_when_tavily_disabled(_reload_config, monkeypatch):
    """Sprint 5: TAVILY_DISABLED + corpus on → fact_checker corpus."""
    monkeypatch.setattr(config, "TAVILY_DISABLED", True)
    monkeypatch.setattr(config, "CORPUS_FC_ENABLED", True)
    assert config.fact_checker_status_mode() == "corpus"


def test_sp0_fc_mode_live_when_tavily_enabled(_reload_config, monkeypatch):
    monkeypatch.setattr(config, "TAVILY_DISABLED", False)
    assert config.tavily_enabled() is True
    assert config.fact_checker_status_mode() == "live"


def test_sp0_fc_mode_stub_without_api_key(_reload_config, monkeypatch):
    monkeypatch.setattr(config, "TAVILY_DISABLED", False)
    monkeypatch.setattr(config, "TAVILY_API_KEY", "")
    monkeypatch.setattr(config, "CORPUS_FC_ENABLED", False)
    assert config.fact_checker_status_mode() == "stub"


def test_sp0_index_html_wires_fact_checker_to_ui():
    """AC-FC-02: index.html consumes fact_checker and shows FC labels."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "fact_checker" in html
    assert "미검증" in html
    assert "문서 내부 검증" in html
    assert "updateBackendStatus" in html
    assert "formatFactCheckerLine" in html
    assert 'id="fc-hint"' in html
