"""Granular dry-run tests (pytest mirror of test_run.py phases)."""

from __future__ import annotations

import pytest

from deconstructor.dry_run.modes import is_depth_cap_headline
from deconstructor.dry_run.scenarios import DEPTH_CAP_SCENARIO, HEADLINE_SCENARIOS
from deconstructor.dry_run.stub import (
    stub_decompose,
    stub_decompose_pass_initial,
    stub_decompose_pass_refine,
    stub_decompose_pass_stuck,
)
from deconstructor.dry_run.subject import parse_subject
from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.routing.after_verify import route_after_verify
from deconstructor.verify.node import verify_node
from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.state_merge import merge_refined_facts
from deconstructor.models import AtomicFact

EXPECTED_SEQUENCE = (
    "deconstruct",
    "verify",
    "deconstruct",
    "verify",
    "skeptic",
    "weaver",
)

# Shared with test_run.py smoke harness
from tests.smoke.constants import EXPECTED_NODE_SEQUENCE as _NODE_SEQ

assert EXPECTED_SEQUENCE == _NODE_SEQ


@pytest.mark.parametrize("scenario", HEADLINE_SCENARIOS, ids=lambda s: s.label)
def test_subject_parser(scenario) -> None:
    assert parse_subject(scenario.headline) == scenario.expected_subject


@pytest.mark.parametrize("scenario", HEADLINE_SCENARIOS, ids=lambda s: s.label)
def test_stub_initial_is_non_atomic(scenario) -> None:
    batch = stub_decompose_pass_initial(scenario.headline)
    assert len(batch.facts) == 1
    assert batch.facts[0].is_atomic is False


@pytest.mark.parametrize("scenario", HEADLINE_SCENARIOS, ids=lambda s: s.label)
def test_stub_refine_is_atomic_pair(scenario) -> None:
    batch = stub_decompose_pass_refine(scenario.headline)
    assert len(batch.facts) == 2
    assert all(f.is_atomic for f in batch.facts)


def test_merge_refined_facts_replaces_parent() -> None:
    parent = AtomicFact(
        id="p1", subject="x", state_change="a -> b", is_atomic=False
    )
    c1 = AtomicFact(subject="a", state_change="s -> 1", is_atomic=True)
    out = merge_refined_facts([parent], "p1", [c1])
    assert len(out) == 1
    assert out[0].id == c1.id


def test_traced_pipeline_node_sequence() -> None:
    traced = run_pipeline_traced("A공장 정전", dry_run=True)
    assert tuple(traced.node_sequence) == EXPECTED_SEQUENCE


def test_traced_pipeline_null_floor() -> None:
    traced = run_pipeline_traced("A공장 정전", dry_run=True)
    assert traced.final_state["extracted_facts"] == []
    assert len(traced.final_state["completed_facts"]) == 2


def test_deconstruct_stub_two_pass_depth() -> None:
    state = {
        "raw_text": "A공장 정전",
        "extracted_facts": [],
        "completed_facts": [],
        "recursion_depth": 0,
        "max_recursion_depth": 5,
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "weaver_result": None,
    }
    d0 = deconstruct_node_stub(state)
    v0 = verify_node({**state, **d0})
    d1 = deconstruct_node_stub({**state, **d0, **v0})
    assert d0["recursion_depth"] == 1
    assert d1["recursion_depth"] == 2
    assert len(d1["extracted_facts"]) == 2


# --- Phase 8: depth cap exhaustion ---


def test_depth_cap_headline_prefix() -> None:
    assert is_depth_cap_headline(DEPTH_CAP_SCENARIO.headline)
    assert parse_subject(DEPTH_CAP_SCENARIO.headline) == "Z공장"


def test_stuck_refine_never_atomic() -> None:
    batch = stub_decompose_pass_stuck("Z공장 정전")
    assert len(batch.facts) == 1
    assert batch.facts[0].is_atomic is False


def test_depth_cap_stub_dispatch() -> None:
    initial = stub_decompose(DEPTH_CAP_SCENARIO.headline, refining=False)
    refined = stub_decompose(DEPTH_CAP_SCENARIO.headline, refining=True)
    assert initial.facts[0].is_atomic is False
    assert refined.facts[0].is_atomic is False


def test_depth_cap_pipeline_leaves_non_atomic() -> None:
    traced = run_pipeline_traced(
        DEPTH_CAP_SCENARIO.headline,
        dry_run=True,
        max_recursion_depth=DEPTH_CAP_SCENARIO.max_recursion_depth,
    )
    st = traced.final_state
    assert len(st["extracted_facts"]) == 1
    assert st["extracted_facts"][0].is_atomic is False
    assert st["completed_facts"] == []
    assert st["recursion_depth"] == DEPTH_CAP_SCENARIO.max_recursion_depth


def test_depth_cap_routes_to_skeptic_not_loop() -> None:
    non_atomic = AtomicFact(
        subject="Z", state_change="compound -> event", is_atomic=False
    )
    state = {
        "raw_text": DEPTH_CAP_SCENARIO.headline,
        "extracted_facts": [non_atomic],
        "completed_facts": [],
        "recursion_depth": 2,
        "max_recursion_depth": 2,
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "weaver_result": None,
    }
    assert route_after_verify(state) == "skeptic"


def test_depth_cap_skeptic_empty_output() -> None:
    traced = run_pipeline_traced(
        DEPTH_CAP_SCENARIO.headline,
        dry_run=True,
        max_recursion_depth=2,
    )
    assert traced.final_state["verified_edges"] == []
    assert traced.final_state["rejected_hypotheses"] == []
