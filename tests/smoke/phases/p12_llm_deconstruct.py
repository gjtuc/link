"""Phase 12 — LLM deconstruct runner (mock)."""

from __future__ import annotations

from unittest.mock import MagicMock

from deconstructor.deconstruct.llm_runner import build_deconstruct_messages, invoke_fact_list
from deconstructor.deconstruct.node import deconstruct_node
from deconstructor.models import AtomicFact, FactList
from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_12_llm_deconstruct(run: StepRunner) -> None:
    run.section("12a message builder")

    msgs = build_deconstruct_messages("test headline")
    run.check("two messages", len(msgs) == 2)
    run.check("headline in user msg", "test headline" in msgs[1].content)

    run.section("12b invoke_fact_list mock")

    mock = MagicMock()
    mock.invoke.return_value = FactList(
        facts=[AtomicFact(subject="g", state_change="p -> o", is_atomic=False)]
    )
    fl = invoke_fact_list("x", llm=mock)
    run.check("mock invoked", mock.invoke.called)
    run.check("fact returned", fl.facts[0].subject == "g")

    run.section("12c deconstruct_node patched")

    def fake_invoke(text, *, llm=None):
        return FactList(
            facts=[AtomicFact(subject="g", state_change="p -> o", is_atomic=False)]
        )

    import deconstructor.deconstruct.node as dn

    original = dn.invoke_fact_list
    dn.invoke_fact_list = fake_invoke
    try:
        out = deconstruct_node(base_state())
        run.check("initial pass depth", out.get("recursion_depth") == 1)
    finally:
        dn.invoke_fact_list = original
