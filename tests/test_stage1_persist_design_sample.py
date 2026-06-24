"""μ-PRE-2b-PERSIST — STAGE-1 persistence boundary design (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "design" / "STAGE-1-PERSIST-spec.md"
CORPUS_SPEC = ROOT / "docs" / "design" / "STAGE-1-CORPUS-spec.md"
BRANCH2B = ROOT / "docs" / "design" / "BRANCH-2b-spec.md"
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "stage1_persist_design_sample.json"


def test_stage1_persist_spec_required_sections():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-PRE-2b-PERSIST" in body
    assert "batch_corpus" in body and "cross_run" in body
    assert "analysis_run_id" in body
    assert "session_id" in body and "run_id" in body and "fact_id" in body
    assert "μ-2b-03" in body
    assert "## NON-GOALS" in body
    assert "MERGE" in body or "재시작" in body


def test_stage1_persist_design_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-PRE-2b-PERSIST"
    assert data["implementation_started"] is False
    assert "namespace" in data
    assert data["namespace"]["analysis_run_id"]
    assert data["migration"]["next_mu"] == "μ-2b-03"


def test_corpus_spec_links_persist_spec():
    body = CORPUS_SPEC.read_text(encoding="utf-8")
    assert "STAGE-1-PERSIST-spec.md" in body


def test_branch2b_spec_documents_persist_mu():
    body = BRANCH2B.read_text(encoding="utf-8")
    assert "μ-PRE-2b-PERSIST" in body
