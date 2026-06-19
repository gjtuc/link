"""
Step 2 — Dreamer LangGraph 노드 (Micro-step S2-6)
==================================================
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.llm_runner import invoke_dream_hypotheses
from deconstructor.agents.dreamer.stub import stub_dream_hypotheses

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-6] {msg}"
    logger.info(line)
    print(line)


def dreamer_node(state: "State", *, dry_run: bool = False) -> dict:
    """
    completed_facts → inferred_facts (source_type=inferred, check_status=pending).

    Args:
        dry_run: True → stub_dream_hypotheses (no LLM).
    """
    _log("dreamer_node enter")
    source_facts = state["completed_facts"]
    headline = state["raw_text"]
    dreamer_log: list[str] = []

    if not source_facts:
        _log("skip: no completed_facts — inferred_facts=[]")
        dreamer_log.append("[DREAM-S2-6] skip: no source facts")
        return {"inferred_facts": [], "dreamer_log": dreamer_log}

    _log(f"source_facts count={len(source_facts)} dry_run={dry_run}")
    dreamer_log.append(f"[DREAM-S2-6] sources={len(source_facts)} dry_run={dry_run}")

    if dry_run:
        _log("routing to stub_dream_hypotheses")
        result = stub_dream_hypotheses(source_facts, raw_text=headline)
    else:
        _log("routing to invoke_dream_hypotheses (live LLM)")
        result = invoke_dream_hypotheses(source_facts, headline=headline)

    inferred = apply_hypotheses(result, source_facts)
    dreamer_log.append(f"[DREAM-S2-6] inferred_facts={len(inferred)}")

    _log(f"dreamer_node exit inferred={len(inferred)}")
    return {
        "inferred_facts": inferred,
        "dreamer_log": dreamer_log,
    }
