"""Tests for verify partition logic."""

from deconstructor.models import AtomicFact
from deconstructor.verify.partition import partition_by_atomicity
from deconstructor.verify.node import verify_node


def test_partition_splits_atomicity():
    atomic = AtomicFact(subject="a", state_change="x -> y", is_atomic=True)
    non = AtomicFact(subject="b", state_change="p -> q", is_atomic=False)
    a, n = partition_by_atomicity([atomic, non])
    assert len(a) == 1
    assert len(n) == 1
    assert a[0].subject == "a"
    assert n[0].subject == "b"


def test_verify_node_state_update():
    atomic = AtomicFact(subject="a", state_change="x -> y", is_atomic=True)
    non = AtomicFact(subject="b", state_change="p -> q", is_atomic=False)
    state = {
        "extracted_facts": [atomic, non],
        "completed_facts": [],
    }
    out = verify_node(state)  # type: ignore[arg-type]
    assert len(out["completed_facts"]) == 1
    assert len(out["extracted_facts"]) == 1
