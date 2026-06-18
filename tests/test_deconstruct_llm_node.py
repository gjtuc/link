"""Mocked LLM tests for deconstruct llm_runner and node."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.deconstruct.llm_runner import (
    build_deconstruct_messages,
    invoke_fact_list,
)
from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.models import AtomicFact, FactList


def _state(**kw):
    base = {
        "raw_text": "B발전소 화재",
        "extracted_facts": [],
        "completed_facts": [],
        "recursion_depth": 0,
        "max_recursion_depth": 5,
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "weaver_result": None,
    }
    base.update(kw)
    return base


def test_build_deconstruct_messages_shape():
    msgs = build_deconstruct_messages("headline text")
    assert len(msgs) == 2
    assert isinstance(msgs[0], SystemMessage)
    assert isinstance(msgs[1], HumanMessage)
    assert "headline text" in msgs[1].content


def test_invoke_fact_list_uses_injected_llm():
    child = AtomicFact(subject="grid", state_change="power -> off", is_atomic=False)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = FactList(facts=[child])

    result = invoke_fact_list("any", llm=mock_llm)

    mock_llm.invoke.assert_called_once()
    assert len(result.facts) == 1
    assert result.facts[0].subject == "grid"


def test_deconstruct_node_initial_pass(monkeypatch):
    child = AtomicFact(subject="grid", state_change="power -> off", is_atomic=False)

    def fake_invoke(text, *, llm=None):
        assert "B발전소 화재" in text
        return FactList(facts=[child])

    monkeypatch.setattr(
        "deconstructor.deconstruct.node.invoke_fact_list",
        fake_invoke,
    )

    out = deconstruct_node(_state())

    assert out["recursion_depth"] == 1
    assert len(out["extracted_facts"]) == 1


def test_deconstruct_node_with_patched_invoke(monkeypatch):
    parent = AtomicFact(
        id="p1",
        subject="grid",
        state_change="power -> off",
        is_atomic=False,
    )
    child_a = AtomicFact(subject="motor", state_change="rpm -> 0", is_atomic=True)
    child_b = AtomicFact(subject="belt", state_change="motion -> stopped", is_atomic=True)

    def fake_invoke(text, *, llm=None):
        assert "grid" in text
        return FactList(facts=[child_a, child_b])

    monkeypatch.setattr(
        "deconstructor.deconstruct.node.invoke_fact_list",
        fake_invoke,
    )

    out = deconstruct_node(_state(extracted_facts=[parent], recursion_depth=1))

    assert out["recursion_depth"] == 2
    assert len(out["extracted_facts"]) == 2
    assert all(f.is_atomic for f in out["extracted_facts"])


def test_deconstruct_node_no_target_returns_empty():
    assert deconstruct_node(_state(recursion_depth=2)) == {}
