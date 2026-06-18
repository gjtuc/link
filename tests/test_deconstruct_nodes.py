"""Tests for deconstruct input resolution and apply."""

from deconstructor.deconstruct.apply import apply_deconstruct_result
from deconstructor.deconstruct.input import resolve_llm_target, resolve_stub_target
from deconstructor.models import AtomicFact, FactList


def _state(**kw):
    base = {
        "raw_text": "A공장 정전",
        "extracted_facts": [],
        "recursion_depth": 0,
    }
    base.update(kw)
    return base


def test_stub_target_initial():
    t = resolve_stub_target(_state())
    assert t is not None
    assert t.text == "A공장 정전"
    assert t.parent_id is None
    assert not t.refining


def test_stub_target_refine():
    parent = AtomicFact(subject="A공장", state_change="power -> lost", is_atomic=False)
    t = resolve_stub_target(_state(extracted_facts=[parent], recursion_depth=1))
    assert t is not None
    assert t.parent_id == parent.id
    assert t.refining


def test_llm_target_refine_uses_subject_pipe():
    parent = AtomicFact(subject="grid", state_change="power -> off", is_atomic=False)
    t = resolve_llm_target(_state(extracted_facts=[parent], recursion_depth=1))
    assert t is not None
    assert t.text == "grid | power -> off"


def test_apply_replaces_parent():
    parent = AtomicFact(id="p1", subject="x", state_change="a -> b", is_atomic=False)
    child = AtomicFact(subject="y", state_change="c -> d", is_atomic=True)
    out = apply_deconstruct_result(
        pending=[parent],
        parent_id="p1",
        result=FactList(facts=[child]),
        recursion_depth=1,
    )
    assert len(out["extracted_facts"]) == 1
    assert out["extracted_facts"][0].id == child.id
    assert out["recursion_depth"] == 2
