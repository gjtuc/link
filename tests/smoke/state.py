"""Minimal pipeline state factory for smoke tests."""

from __future__ import annotations

from deconstructor.dry_run.scenarios import DEFAULT_HEADLINE


def base_state(**overrides: object) -> dict:
    state = {
        "raw_text": DEFAULT_HEADLINE,
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
        "inferred_facts": [],
        "dreamer_log": [],
        "promoted_facts": [],
        "dropped_hypotheses": [],
        "fact_checker_log": [],
        "enable_dreamer": False,
        "weaver_result": None,
    }
    state.update(overrides)
    return state
