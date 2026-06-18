"""Phase 3 — State merge + isolated nodes."""

from __future__ import annotations

from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.models import AtomicFact
from deconstructor.state_merge import merge_refined_facts
from deconstructor.verify.node import verify_node
from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_3_nodes_isolated(run: StepRunner, headline: str) -> None:
    run.section("3a merge_refined_facts")

    parent = AtomicFact(
        id="parent-id",
        subject="X",
        state_change="compound -> event",
        is_atomic=False,
    )
    child_a = AtomicFact(subject="a", state_change="s -> 1", is_atomic=True)
    child_b = AtomicFact(subject="b", state_change="s -> 2", is_atomic=True)
    merged = merge_refined_facts([parent], "parent-id", [child_a, child_b])
    run.check("parent removed", all(f.id != "parent-id" for f in merged))
    run.check("children added", len(merged) == 2)

    run.section("3b verify_node partition")

    mixed = [
        AtomicFact(subject="a", state_change="x -> y", is_atomic=True),
        AtomicFact(subject="b", state_change="p -> q", is_atomic=False),
    ]
    out = verify_node({**base_state(), "extracted_facts": mixed})
    run.check("atomic to completed", len(out["completed_facts"]) == 1)
    run.check("non-atomic stays", len(out["extracted_facts"]) == 1)

    run.section("3c deconstruct_node_stub pass-0")

    s0 = base_state(raw_text=headline, recursion_depth=0)
    d0 = deconstruct_node_stub(s0)
    run.check("depth incremented", d0["recursion_depth"] == 1)
    run.check("one non-atomic extracted", len(d0["extracted_facts"]) == 1)
    run.check("not atomic", d0["extracted_facts"][0].is_atomic is False)

    run.section("3d deconstruct_node_stub pass-1 (refine)")

    s1 = {**s0, **d0}
    v1 = verify_node(s1)
    s2 = {**s1, **v1}
    run.check("verify leaves 1 non-atomic", len(s2["extracted_facts"]) == 1)

    d1 = deconstruct_node_stub(s2)
    run.check("depth==2 after refine", d1["recursion_depth"] == 2)
    run.check("two facts after refine", len(d1["extracted_facts"]) == 2)
    run.check("all atomic after refine", all(f.is_atomic for f in d1["extracted_facts"]))
