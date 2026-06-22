"""
Q1 — skeptic pass-1 node (extracted completed_facts only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from deconstructor.agents.dreamer.pass2_inputs import compute_pass2_gaps
from deconstructor.pipeline.partial_run import detect_partial_run
from deconstructor.skeptic.engine import SkepticEngine
from deconstructor.skeptic.retry import retry_inconclusive
from deconstructor.skeptic.run_log import build_skeptic_log
from deconstructor.web.progress_ctx import progress_sub

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State


def _extracted_completed(completed_facts: list) -> list:
    return [f for f in completed_facts if (f.source_type or "extracted") == "extracted"]


def skeptic_pass1_node(state: "State", *, dry_run: bool = True) -> dict:
    """
    Pass-1 Skeptic: extracted ``completed_facts`` only → ``verified_edges_pass1``.

    Computes ``pass2_gap_nodes`` via ``find_gaps`` for Dreamer pass-2 input (Q1).
    """
    partial = detect_partial_run(
        extracted_facts=state["extracted_facts"],
        completed_facts=state["completed_facts"],
        recursion_depth=state["recursion_depth"],
        max_recursion_depth=state["max_recursion_depth"],
    )

    facts = _extracted_completed(state["completed_facts"])
    print(f"[Q1-skeptic-pass1] evaluating {len(facts)} extracted fact(s) only")

    if len(facts) < 2:
        log = build_skeptic_log(partial, completed_fact_count=len(facts), ran_batch=False)
        gaps = compute_pass2_gaps(facts, [])
        return {
            "partial_run": partial.partial_run,
            "partial_run_reason": partial.reason,
            "verified_edges_pass1": [],
            "pass2_gap_nodes": gaps,
            "skeptic_pass1_log": log,
        }

    engine = SkepticEngine()
    pair_count = len(facts) * (len(facts) - 1)
    with progress_sub(
        "SKEPTIC-PASS1",
        "1차 인과 검증 (extracted)",
        f"facts={len(facts)} pairs≈{pair_count}",
    ):
        batch = engine.evaluate_batch(facts)
    with progress_sub("SKEPTIC-PASS1-RETRY", "INCONCLUSIVE 재검증"):
        batch, retry_log = retry_inconclusive(engine, facts, batch, dry_run=dry_run)

    gaps = compute_pass2_gaps(facts, batch.verified_edges)
    log = build_skeptic_log(partial, completed_fact_count=len(facts), ran_batch=True)
    log.extend(retry_log)

    print(
        f"[Q1-skeptic-pass1] edges={len(batch.verified_edges)} gaps={len(gaps)}"
    )

    return {
        "partial_run": partial.partial_run,
        "partial_run_reason": partial.reason,
        "verified_edges_pass1": batch.verified_edges,
        "pass2_gap_nodes": gaps,
        "skeptic_pass1_log": log,
    }
