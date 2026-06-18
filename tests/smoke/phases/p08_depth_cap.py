"""Phase 8 — Depth cap with non-atomic leftovers."""

from __future__ import annotations

from deconstructor.dry_run.modes import is_depth_cap_headline
from deconstructor.dry_run.scenarios import DEPTH_CAP_SCENARIO
from deconstructor.dry_run.stub import stub_decompose_pass_stuck
from deconstructor.dry_run.subject import parse_subject
from deconstructor.deconstruct.stub_node import deconstruct_node_stub
from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.report import format_traced_report
from deconstructor.routing.after_verify import route_after_verify
from deconstructor.verify.node import verify_node
from tests.smoke.constants import EXPECTED_DEPTH_CAP_SEQUENCE
from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_8_depth_cap(run: StepRunner) -> str:
    scenario = DEPTH_CAP_SCENARIO
    cap = scenario.max_recursion_depth

    run.section("8a depth-cap headline mode")

    run.check("prefix detected", is_depth_cap_headline(scenario.headline))
    run.check(
        "subject parses after prefix",
        parse_subject(scenario.headline) == scenario.expected_subject,
    )

    run.section("8b stuck refine stub never atomic")

    stuck = stub_decompose_pass_stuck(scenario.expected_subject + " 정전")
    run.check("stuck returns 1 fact", len(stuck.facts) == 1)
    run.check("stuck is_atomic=False", stuck.facts[0].is_atomic is False)

    run.section("8c isolated two-pass depth accumulation")

    s0 = base_state(
        raw_text=scenario.headline,
        max_recursion_depth=cap,
        recursion_depth=0,
    )
    d0 = deconstruct_node_stub(s0)
    v0 = verify_node({**s0, **d0})
    run.check("after pass-0: 1 non-atomic extracted", len(v0["extracted_facts"]) == 1)
    run.check("after pass-0: 0 completed", len(v0["completed_facts"]) == 0)

    s1 = {**s0, **d0, **v0}
    d1 = deconstruct_node_stub(s1)
    v1 = verify_node({**s1, **d1})
    run.check("after pass-1: still non-atomic", len(v1["extracted_facts"]) == 1)
    run.check("depth after pass-1", d1["recursion_depth"] == cap)

    run.section("8d route exits loop at cap")

    run.check(
        "verify routes to skeptic not deconstruct",
        route_after_verify({**s1, **d1, **v1}) == "skeptic",
    )

    run.section("8e full traced pipeline incomplete")

    traced = run_pipeline_traced(
        scenario.headline,
        dry_run=True,
        max_recursion_depth=cap,
    )
    st = traced.final_state

    run.check(
        "node sequence unchanged",
        tuple(traced.node_sequence) == EXPECTED_DEPTH_CAP_SEQUENCE,
    )
    run.check("recursion_depth at cap", st["recursion_depth"] == cap)
    run.check("non-atomic leftover", len(st["extracted_facts"]) == 1)
    run.check(
        "leftover is_atomic=False",
        st["extracted_facts"][0].is_atomic is False,
    )
    run.check("no completed facts", len(st["completed_facts"]) == 0)
    run.check("null floor NOT reached", not scenario.expect_null_floor)

    run.section("8f skeptic partial_run logging")

    run.check("partial_run True", st["partial_run"] is True)
    run.check(
        "reason depth_cap",
        st["partial_run_reason"] == "depth_cap_non_atomic_remain",
    )
    codes = [e.code for e in st["skeptic_log"]]
    run.check("PARTIAL_INPUT logged", "PARTIAL_INPUT" in codes)
    run.check("DEPTH_CAP_TRUNCATION logged", "DEPTH_CAP_TRUNCATION" in codes)
    run.check("INSUFFICIENT_FACTS logged", "INSUFFICIENT_FACTS" in codes)

    run.section("8g weaver console skip")

    wr = st["weaver_result"]
    run.check("weaver ran", wr is not None)
    run.check("weaver mode console", wr.mode == "console")
    run.check("weaver 0 edges", wr.edges_written == 0)
    run.check("weaver partial flag", wr.partial_run is True)

    run.section("8h report shows INCOMPLETE status")

    report = format_traced_report(traced)
    run.check("INCOMPLETE in report", "INCOMPLETE" in report)
    run.check("depth cap in report", "depth cap hit" in report)

    return report
