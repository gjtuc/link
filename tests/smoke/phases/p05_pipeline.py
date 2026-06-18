"""Phase 5 — Full traced pipeline."""

from __future__ import annotations

from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.report import format_traced_report
from tests.smoke.constants import EXPECTED_NODE_SEQUENCE
from tests.smoke.harness import StepRunner


def phase_5_traced_pipeline(run: StepRunner, headline: str) -> str:
    run.section("5a traced run completes")

    traced = run_pipeline_traced(headline, dry_run=True)
    state = traced.final_state
    run.check("final state dict", isinstance(state, dict))

    run.section("5b node visit sequence")

    seq = traced.node_sequence
    run.check("5 node steps", len(seq) == 6, f"got {seq}")
    run.check(
        "exact sequence",
        tuple(seq) == EXPECTED_NODE_SEQUENCE,
        f"got {seq}",
    )

    run.section("5c deconstruct loop depth")

    run.check("recursion_depth==2", state["recursion_depth"] == 2)

    run.section("5d null floor")

    run.check("no extracted leftovers", state["extracted_facts"] == [])
    run.check("two completed facts", len(state["completed_facts"]) == 2)

    run.section("5e atomic invariants")

    for i, fact in enumerate(state["completed_facts"]):
        run.check(f"fact[{i}] is_atomic", fact.is_atomic is True)
        run.check(f"fact[{i}] has subject", bool(fact.subject))
        run.check(f"fact[{i}] has state_change", bool(fact.state_change))

    run.section("5f skeptic output shape")

    run.check("verified_edges is list", isinstance(state["verified_edges"], list))
    run.check(
        "rejected_hypotheses is list",
        isinstance(state["rejected_hypotheses"], list),
    )
    run.check(">=1 verified edge", len(state["verified_edges"]) >= 1)
    run.check(">=1 rejected", len(state["rejected_hypotheses"]) >= 1)

    edge = state["verified_edges"][0]
    run.check("edge has probability", 0.0 < edge.probability <= 1.0)
    run.check("edge has latency ms", edge.latency is not None and edge.latency > 0)

    run.section("5g report sections")

    report = format_traced_report(traced)
    for section in (
        "PIPELINE TRACE",
        "ATOMIC FACTS",
        "VERIFIED CAUSAL EDGES",
        "REJECTED HYPOTHESES",
        "SKEPTIC LOG",
        "WEAVER",
    ):
        run.check(f"report contains [{section}]", section in report)

    return report
