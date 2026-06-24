"""μ-2b-ω — Branch-2b STAGE-1 corpus 1차 마감 (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = FIXTURES / "b2b_closure_sample.json"
SPEC = ROOT / "docs" / "design" / "BRANCH-2b-spec.md"
ROADMAP = ROOT / "docs" / "design" / "STAGE-0-CLOSURE-ROADMAP.md"
HANDOFF = ROOT / "docs" / "design" / "SUPERVISOR-AI-HANDOFF.md"
CORPUS_SPEC = ROOT / "docs" / "design" / "STAGE-1-CORPUS-spec.md"
PERSIST_SPEC = ROOT / "docs" / "design" / "STAGE-1-PERSIST-spec.md"

CORPUS_MODULES = [
    ROOT / "deconstructor" / "corpus" / "contract.py",
    ROOT / "deconstructor" / "corpus" / "memory_store.py",
    ROOT / "deconstructor" / "corpus" / "ingest_hook.py",
    ROOT / "deconstructor" / "corpus" / "query.py",
    ROOT / "deconstructor" / "corpus" / "status_block.py",
    ROOT / "deconstructor" / "corpus" / "store_protocol.py",
    ROOT / "deconstructor" / "corpus" / "memory_adapter.py",
    ROOT / "deconstructor" / "corpus" / "factory.py",
    ROOT / "deconstructor" / "corpus" / "neo4j_adapter.py",
]


def test_b2b_closure_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-2b-ω"
    assert data["closure"] == "1차 마감"
    assert data["live_e2e_rerun"] is False
    assert data["branch_3_locked"] is True
    assert data["backends"]["default"] == "memory"
    assert set(data["backends"]["implemented"]) == {"memory", "neo4j"}
    assert "LINK_CROSS_RUN_CORPUS" in data["env_flags"]
    assert "LINK_CORPUS_BACKEND" in data["env_flags"]
    assert "μ-2b-03-01" in data["stack_completed"]
    assert "μ-2b-02-UI" in data["stack_completed"]
    assert "μ-2b-02-UI" not in data["deferred"]


def test_b2b_closure_stack_modules_exist():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert len(data["stack_completed"]) >= 9
    for path in CORPUS_MODULES:
        assert path.is_file(), f"missing corpus module: {path.name}"
    for rel in data["offline_pytest_modules"]:
        assert (ROOT / rel).is_file(), rel


def test_branch2b_spec_documents_b2b_omega():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-2b-ω" in body
    assert "1차 마감" in body
    assert "b2b_closure_sample.json" in body
    assert "μ-2b-03-01" in body


def test_roadmap_branch2b_first_closure():
    body = ROADMAP.read_text(encoding="utf-8")
    assert "μ-2b-ω" in body
    assert "Branch-2b" in body
    assert "STAGE-1" in body or "cross-run corpus" in body


def test_handoff_documents_b2b_omega_complete():
    body = HANDOFF.read_text(encoding="utf-8")
    assert "μ-2b-ω" in body or "μ-2b-02-UI-FIX" in body
    assert "μ-2b-02-UI" in body


def test_corpus_and_persist_specs_reference_stack():
    corpus = CORPUS_SPEC.read_text(encoding="utf-8")
    persist = PERSIST_SPEC.read_text(encoding="utf-8")
    assert "μ-2b-02-API" in corpus
    assert "μ-2b-03-00" in persist
    assert "μ-2b-03-01" in persist
