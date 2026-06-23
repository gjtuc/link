"""μ-PRE-2b-03 — Branch-2b design sample (offline)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = Path(__file__).resolve().parent / "fixtures" / "branch2b_design_sample.json"
SPEC = ROOT / "docs" / "design" / "BRANCH-2b-spec.md"
ROADMAP = ROOT / "docs" / "design" / "STAGE-0-CLOSURE-ROADMAP.md"
HANDOFF = ROOT / "docs" / "design" / "SUPERVISOR-AI-HANDOFF.md"


def test_branch2b_design_sample_schema():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert data["mu_id"] == "μ-PRE-2b-00"
    assert data["branch"] == "Branch-2b"
    assert data["status"] == "design_only"
    assert data["implementation_started"] is False
    assert "branch_2b_unlocked" in data["unlock_fields_proposed"]
    assert "μ-UNLOCK-2b" in data["mu_ids_planned"]
    assert "μ-2b-ω" in data["mu_ids_planned"]


def test_branch2b_spec_exists_with_required_sections():
    assert SPEC.is_file()
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-PRE-2b-00" in body
    assert "## 1차 목표" in body
    assert "STAGE 1" in body or "STAGE-1" in body
    assert "cross-run corpus" in body
    assert "## NON-GOALS" in body
    assert "Branch-3" in body
    assert "μ-UNLOCK-2b" in body
    assert "branch_2b_unlocked" in body
    assert "BRANCH-2a-spec.md" in body
    assert "BRANCH-0-MAINTENANCE-spec.md" in body


def test_branch2b_spec_mu_table_all_pending_except_pre():
    body = SPEC.read_text(encoding="utf-8")
    assert "μ-2b-00" in body
    assert "μ-2b-01" in body
    assert "[ ]" in body
    assert "MUST 승격" in body or "MUST 검토" in body


def test_roadmap_wave4_design_locked_implementation():
    body = ROADMAP.read_text(encoding="utf-8")
    assert "μ-PRE-2b" in body
    assert "2b" in body
    assert "잠금" in body or "구현" in body


def test_handoff_next_unlock_after_approval():
    body = HANDOFF.read_text(encoding="utf-8")
    assert "μ-PRE-2b" in body
    assert "μ-UNLOCK-2b" in body or "승인" in body
