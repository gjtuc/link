"""
Branch gate tests — each branch proven by pytest (LLM-free where possible).

Branch-0: Phase R + S1-READ blocks pipeline before LLM.
Branch-1: Phase R prerequisite; full E2E = scripts/branch1_full_e2e.py (quota).
Branch-2+: locked via tests/fixtures/branch_state.json + forbidden spec globs.

Ingest touch → run: python scripts/phase_r_regression.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deconstructor.web.extract import ExtractedSource, expand_document_sources, from_text
from deconstructor.web.ingest_verify import verify_read
from tests.ingest_manifest import (
    BRANCH_STATE_PATH,
    FORBIDDEN_BRANCH2_GLOBS,
    INGEST_TOUCH_PATHS,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs" / "design"
STATE_FILE = ROOT / BRANCH_STATE_PATH


def _branch_state() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _document_mode(monkeypatch):
    monkeypatch.setenv("LINK_DOCUMENT_INGEST", "document")
    import deconstructor.web.extract as ex

    monkeypatch.setattr(ex, "DOCUMENT_INGEST_MODE", "document")
    monkeypatch.setattr(ex, "_use_document_deconstruct_ingest", lambda: True)


# --- Gate: branch lock (pytest, not docs) ---


def test_gate_branch_state_file_valid():
    s = _branch_state()
    assert s["branch_0"] == "active"
    assert isinstance(s["branch_1_complete"], bool)
    assert isinstance(s["branch_2_unlocked"], bool)


def test_gate_branch2_specs_forbidden_while_locked():
    """Branch-2a/2b/3: no spec files until branch_2_unlocked."""
    if _branch_state().get("branch_2_unlocked"):
        pytest.skip("branch_2_unlocked")
    found: list[str] = []
    for pattern in FORBIDDEN_BRANCH2_GLOBS:
        found.extend(p.name for p in DESIGN.glob(pattern))
    assert found == [], f"locked branch specs exist: {found}"


def test_gate_branch1_state_consistent_with_lock():
    """branch_2 stays locked; branch_1 reflects E2E outcome."""
    s = _branch_state()
    assert s["branch_2_unlocked"] is False
    assert isinstance(s["branch_1_complete"], bool)


def test_gate_branch1_complete_post_e2e():
    """After branch1_full_e2e exit 0: branch_1_complete=true, branch_2 still locked."""
    s = _branch_state()
    assert s["branch_1_complete"] is True
    assert s["branch_2_unlocked"] is False


def test_gate_ingest_manifest_files_exist():
    """Ingest touch list — phase_r_regression.py when these change."""
    missing = [p for p in INGEST_TOUCH_PATHS if not (ROOT / p).is_file()]
    assert missing == [], missing


def test_gate_pipeline_imports_verify_read():
    import deconstructor.web.pipeline_batch as pb

    assert hasattr(pb, "run_pipeline_batch")
    source = Path(pb.__file__).read_text(encoding="utf-8")
    assert "verify_read" in source
    assert "S1-READ" in source


# --- Branch-0: read gate MUST block Phase A ---


def test_branch0_mu_r_gate_01_f0_a2_blocks_read():
    """μ-R-GUARD-01: contract violation (NG-1 symptom) → read not ok."""
    bad = [
        ExtractedSource(
            kind="document",
            label="paper.pdf",
            text="x" * 50,
            source_file="paper.pdf",
            chunk_id="paper.pdf#chunk-1/1",
            chunk_index=1,
            chunk_total=1,
            document_page_count=10,
        )
    ]
    report = verify_read(bad)
    assert not report.ok
    assert report.blocking


def test_branch0_mu_r_gate_02_missing_source_file_fails_must():
    """μ-R-META-01: slight C-2 break → MUST fail before analyze."""
    broken = [
        ExtractedSource(
            kind="text",
            label="draft.txt",
            text="Valid paragraph with enough content for read check. " * 5,
            source_file="",
            chunk_id="#chunk-1/1",
            chunk_index=1,
            chunk_total=1,
        )
    ]
    report = verify_read(broken)
    meta_fails = [c for c in report.checks if c.id.startswith("μ-R-META-01:") and not c.ok]
    assert meta_fails
    assert not report.ok


def test_branch0_s1_read_blocks_pipeline_no_llm(monkeypatch):
    """S1-READ: failed read_verify → run_pipeline_with_steps never called."""
    from deconstructor.web import pipeline_batch

    calls: list = []

    def _no_llm(*args, **kwargs):
        calls.append(1)
        raise AssertionError("LLM pipeline must not run when Phase R fails")

    monkeypatch.setattr(pipeline_batch, "run_pipeline_with_steps", _no_llm)

    bad = [
        ExtractedSource(
            kind="document",
            label="paper.pdf",
            text="tiny",
            source_file="paper.pdf",
            chunk_id="paper.pdf#chunk-1/1",
            chunk_index=1,
            chunk_total=1,
            document_page_count=8,
        )
    ]
    result = pipeline_batch.run_pipeline_batch(bad)
    assert result.get("failed_step") == "S1-READ"
    assert "read_verify" in result
    assert result["read_verify"]["ok"] is False
    assert calls == []


def test_branch0_read_verify_ok_before_analyze():
    """Valid ingest → Phase R ok (prerequisite for any Phase A)."""
    sources = expand_document_sources(
        "ok.txt",
        "Ni catalyst loading increased under test conditions. " * 10,
        kind="text",
        source_file="ok.txt",
    )
    report = verify_read(sources)
    assert report.ok
    payload = report.to_dict()
    assert payload["ok"] is True
    assert payload["passed"] > 0
    assert any(c.id == "μ-R-MODE-01" and c.ok for c in report.checks)


def test_branch0_regression_scripts_exist():
    """T-READ-ALL entrypoints present."""
    assert (ROOT / "scripts" / "phase_r_regression.py").is_file()
    assert (ROOT / "scripts" / "ingest_read_verify.py").is_file()


# --- Branch-1: readiness (Phase R done; Phase A = quota manual) ---


def test_branch1_prerequisite_s0b_phase_r():
    """Branch-1 step 1-1: S0-B fixtures must pass Phase R before full E2E."""
    short = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
    long = ROOT / "tests" / "fixtures" / "s0b_draft_long.txt"
    if not short.is_file():
        pytest.skip("generate_s0bc_fixtures.py")
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
    assert report.ok, report.to_dict()


def test_branch1_prerequisite_s0c_phase_r():
    """Branch-1 step 1-2: S0-C fixtures must pass Phase R."""
    paper = ROOT / "tests" / "fixtures" / "s0c_paper.txt"
    memo = ROOT / "tests" / "fixtures" / "s0c_memo.txt"
    if not paper.is_file():
        pytest.skip("generate_s0bc_fixtures.py")
    pt = paper.read_text(encoding="utf-8")
    mt = memo.read_text(encoding="utf-8")
    sources = expand_document_sources(paper.name, from_text(pt), kind="document", source_file=paper.name)
    sources += expand_document_sources(memo.name, from_text(mt), kind="document", source_file=memo.name)
    report = verify_read(sources, raw_by_file={paper.name: pt, memo.name: mt})
    assert report.ok


def test_branch1_e2e_scripts_exist():
    assert (ROOT / "scripts" / "s0b_e2e_run.py").is_file()
    assert (ROOT / "scripts" / "s0c_e2e_run.py").is_file()
    assert (ROOT / "scripts" / "branch1_full_e2e.py").is_file()


def test_branch1_mu_a_ids_in_spec():
    """μ-A-B/C IDs — Branch-1 checklist (minimal spec surface)."""
    spec = (DESIGN / "BRANCH-1-spec.md").read_text(encoding="utf-8")
    for mid in ("μ-A-B-PIPE-01", "μ-A-C-ORC-01", "μ-A-C-UI-01"):
        assert mid in spec
