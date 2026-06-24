"""μ-PROBE-00 — capability catalog probe script (offline)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "capability_catalog_probe.py"
SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
S0A = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"
SPEC = ROOT / "docs" / "design" / "CAPABILITY-PROBE-spec.md"


def test_probe_script_exists():
    assert PROBE.is_file()
    text = PROBE.read_text(encoding="utf-8")
    assert "neo4j-off" in text
    assert "pdf-triple" in text
    assert "scanned-pdf" in text
    assert "log_capability_run" in text
    assert "capability_probes" in text


def test_probe_fixture_paths():
    assert SHORT.is_file()
    assert S0A.is_file() or (ROOT / "scripts" / "generate_s0a_fixture.py").is_file()


def test_probe_spec_documents_mu_ids():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-PROBE-01" in body
    assert "cat-neo4j-off" in body
    assert "cat-pdf-triple" in body
    assert "cat-scanned-pdf" in body


def test_probe_script_skip_phase_r_flag():
    text = PROBE.read_text(encoding="utf-8")
    assert "skip-phase-r" in text or "skip_phase_r" in text
