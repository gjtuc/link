"""pipeline_link state merge + step codes."""

from deconstructor.web.pipeline_link import _merge_pipeline_update, run_pipeline_with_steps


def test_merge_completed_facts():
    base = {"completed_facts": [{"id": "a"}], "raw_text": "x"}
    update = {"completed_facts": [{"id": "b"}], "recursion_depth": 1}
    merged = _merge_pipeline_update(base, update)
    assert len(merged["completed_facts"]) == 2
    assert merged["recursion_depth"] == 1


def test_run_pipeline_with_steps_dry_run():
    from deconstructor.web.link_steps import LinkStepTracker

    tracker = LinkStepTracker()
    state = run_pipeline_with_steps(
        tracker,
        1,
        "Test headline for pipeline.",
        dry_run=True,
        enable_dreamer=True,
        fact_checker_dry_run=True,
    )
    steps = [s["step"] for s in tracker.to_list()]
    assert "S4-1-COMPILE" in steps
    assert "S4-1-NODE-deconstruct" in steps
    assert "S4-1-DONE" in steps
    assert state.get("raw_text")
