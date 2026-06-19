"""Human hypothesis MVP — factory·스키마 단위 테스트."""

from __future__ import annotations

import pytest

from deconstructor.web.human_hypothesis.factory import build_human_inferred_fact
from deconstructor.web.human_hypothesis.schemas import HumanHypothesisCreate
from deconstructor.web.human_hypothesis.store import (
    HumanHypothesisStoreError,
    load_anchor_fact,
)


def test_human_hypothesis_create_strips_whitespace():
    payload = HumanHypothesisCreate(
        anchor_fact_id=" fact_01 ",
        subject=" Test subject ",
        state_change=" increased ",
        mechanism=" because ",
    )
    assert payload.anchor_fact_id == "fact_01"
    assert payload.subject == "Test subject"


def test_build_human_inferred_fact_provenance():
    payload = HumanHypothesisCreate(
        anchor_fact_id="fact_01",
        subject="Electrolyte resistance",
        state_change="increased",
        mechanism="Longer sintering reduces conductivity.",
    )
    fact = build_human_inferred_fact(payload)
    assert fact.source_type == "inferred"
    assert fact.check_status == "pending"
    assert fact.author == "human"
    assert fact.anchor_fact_id == "fact_01"
    assert fact.is_atomic is True
    assert "sintering" in fact.reasoning


def test_load_anchor_fact_missing_raises():
    """Neo4j 없을 때는 연결 오류; id 없으면 HumanHypothesisStoreError."""
    pytest.importorskip("neo4j")
    from deconstructor.viz.neo4j_utils import neo4j_is_available

    if not neo4j_is_available():
        pytest.skip("Neo4j not available")
    with pytest.raises(HumanHypothesisStoreError, match="찾을 수 없습니다"):
        load_anchor_fact("nonexistent-anchor-id-00000000")
