"""
Sprint 3 — deconstruct depth & density (SP3-TEST-01).

See ``docs/design/SPRINT-3-deconstruct-depth-spec.md``.
"""

from __future__ import annotations

import pytest

from deconstructor.deconstruct.density_hints import min_facts_for_text
from deconstructor.deconstruct.llm_runner import build_deconstruct_messages
from deconstructor.models import AtomicFact
from deconstructor.verify.compound_heuristic import apply_compound_heuristic, looks_compound
from deconstructor.verify.node import verify_node


def test_sp3_prm03_min_facts_for_long_chunk():
    assert min_facts_for_text("x" * 8000) >= 5
    assert min_facts_for_text("short") == 2


def test_sp3_prm03_density_hint_in_messages():
    long_text = "word " * 1500
    msgs = build_deconstruct_messages(long_text)
    user = msgs[1].content
    assert "at least" in user.lower() or "8000" in user or str(min_facts_for_text(long_text)) in user


def test_sp3_heu01_compound_subject():
    fact = AtomicFact(
        subject="Ni catalyst and support",
        state_change="loading -> increased",
        is_atomic=True,
    )
    assert looks_compound(fact)


def test_sp3_heu02_verify_keeps_non_atomic_for_reloop():
    compound = AtomicFact(
        subject="A and B",
        state_change="state -> changed",
        is_atomic=True,
    )
    adjusted = apply_compound_heuristic([compound])
    assert adjusted[0].is_atomic is False
    state = {
        "extracted_facts": adjusted,
        "completed_facts": [],
        "source_document_meta": {},
    }
    out = verify_node(state)  # type: ignore[arg-type]
    assert len(out["extracted_facts"]) == 1
    assert len(out["completed_facts"]) == 0


def test_sp3_tst02_dry_run_recursion_depth():
    from deconstructor.web.link_steps import LinkStepTracker
    from deconstructor.web.pipeline_link import run_pipeline_with_steps

    state = run_pipeline_with_steps(
        LinkStepTracker(),
        1,
        "Grid outage at factory A.",
        dry_run=True,
        enable_dreamer=False,
        fact_checker_dry_run=True,
    )
    assert state.get("recursion_depth", 0) >= 2


def test_sp3_obs_debug_batch_metrics():
    from deconstructor.web.debug_report import build_pipeline_debug, summarize_single_state
    from deconstructor.viz.neo4j_utils import GraphFetchResult

    state = {
        "raw_text": "x" * 100,
        "completed_facts": [],
        "recursion_depth": 2,
        "max_recursion_depth": 5,
        "partial_run": False,
        "partial_run_reason": "",
        "source_document_meta": {"chunk_id": "a#chunk-1/2"},
    }
    summary = summarize_single_state(state)
    assert summary["deconstruct"]["recursion_depth"] == 2
    assert summary["source_document_meta"]["chunk_id"] == "a#chunk-1/2"

    debug = build_pipeline_debug(
        [state, {**state, "recursion_depth": 1, "completed_facts": []}],
        fetched=GraphFetchResult([], [], 0, False, None),
        batch_run_id="run",
        fact_checker_mode="stub",
    )
    assert debug["deconstruct_batch"]["runs_with_depth_gt_1"] == 1


@pytest.mark.expensive
def test_sp3_e2e_llm_density_optional():
    """Optional live LLM — skip in CI unless explicitly run."""
    pytest.importorskip("langchain_core")
    from deconstructor.deconstruct.llm_runner import invoke_fact_list

    text = ("Ni loading on catalyst increased conversion. " * 40).strip()
    result = invoke_fact_list(text, min_facts_hint=min_facts_for_text(text))
    assert len(result.facts) >= 2
