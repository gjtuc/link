"""debug_report 단위 테스트."""

from __future__ import annotations

from deconstructor.models import AtomicFact
from deconstructor.web.debug_report import summarize_single_state


def test_summarize_flags_zero_completed():
    state = {
        "raw_text": "hello",
        "analysis_run_id": "run-1",
        "completed_facts": [],
        "promoted_facts": [],
        "dropped_hypotheses": [],
        "verified_edges": [],
    }
    s = summarize_single_state(state)
    assert s["counts"]["completed_facts"] == 0
    assert any("completed_facts=0" in h for h in s["diagnosis"])


def test_summarize_orphan_extracted():
    fact = AtomicFact(
        subject="criminal",
        state_change="fired gun",
        is_atomic=True,
        source_type="extracted",
        check_status="active",
    )
    state = {
        "raw_text": "crime",
        "analysis_run_id": "run-2",
        "completed_facts": [fact],
        "promoted_facts": [],
        "dropped_hypotheses": [],
        "verified_edges": [],
    }
    s = summarize_single_state(state)
    assert s["weaver_would_persist"]["orphan_extracted"] == 1
    assert s["samples"]["orphan_extracted"][0]["source_type"] == "extracted"
