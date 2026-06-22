"""μ-Q1-06 — 2-pass Dreamer dry-run pipeline smoke."""

from deconstructor.agents.dreamer.pass2_inputs import select_pass2_source_facts
from deconstructor.graph.builder import run_pipeline


def test_q1_two_pass_dry_run_smoke():
    result = run_pipeline(
        "[단독] 10:00 A공장 정전이 발생했다.",
        dry_run=True,
        enable_dreamer=True,
        persist_db=False,
    )
    assert result.get("ok", True) is not False
    assert "verified_edges_pass1" in result
    assert isinstance(result["verified_edges_pass1"], list)
    assert "pass2_gap_nodes" in result
    assert len(result.get("promoted_facts", [])) >= 1
    dreamer_log = "\n".join(result.get("dreamer_log") or [])
    assert "pass2_source_count=" in dreamer_log
    assert "pass2_gap_count=" in dreamer_log

    pass2 = select_pass2_source_facts(
        result["completed_facts"],
        result["verified_edges_pass1"],
        gap_nodes=result.get("pass2_gap_nodes"),
    )
    pass2_ids = {f.id for f in pass2}
    for f in pass2:
        assert (f.source_type or "extracted") == "extracted"
    log_count = None
    for line in result.get("dreamer_log") or []:
        if "pass2_source_count=" in line:
            log_count = int(line.split("pass2_source_count=")[1].split()[0])
    assert log_count == len(pass2_ids)
