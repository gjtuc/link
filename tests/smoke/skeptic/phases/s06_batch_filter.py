"""Skeptic smoke phase 6 — batch bidirectional filter."""

from __future__ import annotations

from deconstructor.models import CausalEdge
from deconstructor.skeptic.batch_filter import resolve_bidirectional_conflicts
from tests.smoke.harness import StepRunner


def phase_batch_filter(run: StepRunner) -> None:
    run.section("6 Batch bidirectional filter (R12)")
    edges = [
        CausalEdge(source_fact_id="a", target_fact_id="b", probability=0.9, latency=100),
        CausalEdge(source_fact_id="b", target_fact_id="a", probability=0.6, latency=100),
    ]
    out = resolve_bidirectional_conflicts(edges)
    run.ok("one edge kept", len(out) == 1)
    run.ok("higher prob wins", out[0].probability == 0.9)
    run.ok("direction a->b", out[0].source_fact_id == "a")
