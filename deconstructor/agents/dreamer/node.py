"""
Step 2 — Dreamer LangGraph 노드 (Micro-step S2-6)
==================================================

Q1: pass-2 sources from ``select_pass2_source_facts`` (endpoints + Gap).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.llm_runner import invoke_dream_hypotheses
from deconstructor.agents.dreamer.pass2_inputs import select_pass2_source_facts
from deconstructor.agents.dreamer.schemas import PRO_HYPOTHESIS_MAX

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-6] {msg}"
    logger.info(line)
    print(line)


def _resolve_pass2_sources(state: "State") -> list:
    """Q1 2-pass: narrow sources; legacy 1-pass uses all completed_facts."""
    if state.get("enable_dreamer") and state.get("verified_edges_pass1") is not None:
        return select_pass2_source_facts(
            state["completed_facts"],
            state.get("verified_edges_pass1") or [],
            gap_nodes=state.get("pass2_gap_nodes"),
        )
    return list(state["completed_facts"])


def dreamer_node(state: "State", *, dry_run: bool = False) -> dict:
    """
    completed_facts (or Q1 pass2 subset) → inferred_facts.
    """
    _log("dreamer_node enter")
    source_facts = _resolve_pass2_sources(state)
    headline = state["raw_text"]
    dreamer_log: list[str] = []

    gap_count = len(state.get("pass2_gap_nodes") or [])
    dreamer_log.append(
        f"[DREAM-S2-6] pass2_source_count={len(source_facts)} pass2_gap_count={gap_count}"
    )
    _log(f"pass2_source_count={len(source_facts)} pass2_gap_count={gap_count}")

    if not source_facts:
        _log("skip: no pass2 source facts — inferred_facts=[]")
        dreamer_log.append("[DREAM-S2-6] skip: no source facts")
        return {"inferred_facts": [], "dreamer_log": dreamer_log}

    _log(f"source_facts count={len(source_facts)} dry_run={dry_run}")
    dreamer_log.append(f"[DREAM-S2-6] sources={len(source_facts)} dry_run={dry_run}")

    if dry_run:
        _log("routing to stub 2-stage (flash→pro)")
        from deconstructor.agents.dreamer.stub import stub_flash_breadth, stub_pro_compress

        broad = stub_flash_breadth(source_facts, raw_text=headline)
        dreamer_log.append(
            f"[DREAM-S2-6] flash breadth={len(broad.hypotheses)}"
        )
        result = stub_pro_compress(source_facts, broad, raw_text=headline)
    else:
        _log("routing to live 2-stage (flash→pro)")
        result = invoke_dream_hypotheses(source_facts, headline=headline)

    dreamer_log.append(
        f"[DREAM-S2-6] pro finalists={len(result.hypotheses)} "
        f"(max {PRO_HYPOTHESIS_MAX} for fact_checker)"
    )
    inferred = apply_hypotheses(result, source_facts)
    dreamer_log.append(f"[DREAM-S2-6] inferred_facts={len(inferred)}")

    _log(f"dreamer_node exit inferred={len(inferred)}")
    return {
        "inferred_facts": inferred,
        "dreamer_log": dreamer_log,
    }
