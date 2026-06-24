"""Tests for routing.after_verify."""

from deconstructor.routing.after_verify import route_after_verify
from deconstructor.models import AtomicFact


def _state(**kw):
    base = {
        "extracted_facts": [],
        "recursion_depth": 1,
        "max_recursion_depth": 5,
    }
    base.update(kw)
    return base


def test_null_floor_to_skeptic():
    assert route_after_verify(_state()) == "skeptic"


def test_null_floor_to_skeptic_pass1_when_enabled():
    assert route_after_verify(_state(enable_dreamer=True)) == "skeptic_pass1"


def test_non_atomic_loops():
    non = AtomicFact(subject="x", state_change="a -> b", is_atomic=False)
    assert route_after_verify(_state(extracted_facts=[non], recursion_depth=2)) == "deconstruct"


def test_cap_to_skeptic():
    non = AtomicFact(subject="x", state_change="a -> b", is_atomic=False)
    assert (
        route_after_verify(
            _state(extracted_facts=[non], recursion_depth=5, max_recursion_depth=5)
        )
        == "skeptic"
    )
