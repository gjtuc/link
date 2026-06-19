"""Step 1 — Provenance 스키마·태깅 단위 테스트."""

import pytest

from deconstructor.models import AtomicFact
from deconstructor.provenance.assign import tag_as_extracted
from deconstructor.provenance.types import (
    validate_check_status,
    validate_source_type,
    is_ghost_dropped,
)
from deconstructor.verify.node import verify_node


def test_atomic_fact_defaults_extracted():
    fact = AtomicFact(subject="grid", state_change="power -> off", is_atomic=True)
    assert fact.source_type == "extracted"
    assert fact.check_status == "active"


def test_validate_source_type_rejects_invalid():
    with pytest.raises(ValueError, match="source_type"):
        validate_source_type("hallucinated")


def test_validate_check_status_rejects_invalid():
    with pytest.raises(ValueError, match="check_status"):
        validate_check_status("unknown")


def test_is_ghost_dropped_only_inferred_dropped():
    assert is_ghost_dropped("inferred", "dropped") is True
    assert is_ghost_dropped("inferred", "pending") is False
    assert is_ghost_dropped("extracted", "dropped") is False


def test_tag_as_extracted_sets_provenance():
    fact = AtomicFact(
        subject="a",
        state_change="x -> y",
        is_atomic=True,
        source_type="inferred",
        check_status="pending",
    )
    tagged = tag_as_extracted([fact])
    assert len(tagged) == 1
    assert tagged[0].source_type == "extracted"
    assert tagged[0].check_status == "active"


def test_verify_node_tags_completed_as_extracted():
    atomic = AtomicFact(subject="a", state_change="x -> y", is_atomic=True)
    non = AtomicFact(subject="b", state_change="p -> q", is_atomic=False)
    state = {
        "extracted_facts": [atomic, non],
        "completed_facts": [],
    }
    out = verify_node(state)  # type: ignore[arg-type]
    completed = out["completed_facts"][0]
    assert completed.source_type == "extracted"
    assert completed.check_status == "active"


def test_model_rejects_invalid_source_type_on_construct():
    with pytest.raises(ValueError):
        AtomicFact(
            subject="x",
            state_change="a -> b",
            source_type="invalid",  # type: ignore[arg-type]
        )
