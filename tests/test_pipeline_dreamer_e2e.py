"""Step 4 — pipeline wiring integration test."""

from deconstructor.graph.builder import run_pipeline


def test_enable_dreamer_dry_run_pipeline():
    result = run_pipeline(
        "[단독] 10:00 A공장 정전이 발생했다.",
        dry_run=True,
        enable_dreamer=True,
        persist_db=False,
    )
    assert len(result.get("inferred_facts", [])) == 0  # consumed by fact_checker
    assert len(result.get("promoted_facts", [])) == 2
    assert len(result.get("dropped_hypotheses", [])) == 1
    assert result["dropped_hypotheses"][0].ghost_fact.check_status == "dropped"
