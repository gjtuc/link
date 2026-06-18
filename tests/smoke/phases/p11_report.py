"""Phase 11 — Report section package."""

from __future__ import annotations

from deconstructor.pipeline_trace import run_pipeline_traced
from deconstructor.report.compose import format_dry_run_report
from deconstructor.report.sections.atomic_facts import format_atomic_facts_section
from deconstructor.report.sections.header import format_header_section
from deconstructor.report.sections.status import format_status_line
from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_11_report_sections(run: StepRunner, headline: str) -> None:
    run.section("11a header + status sections")

    st = base_state(raw_text=headline, recursion_depth=2)
    hdr = "\n".join(format_header_section(st))
    run.check("header has REPORT", "PIPELINE REPORT" in hdr)
    run.check("status complete", "COMPLETE" in format_status_line(st))

    run.section("11b traced report all section tags")

    traced = run_pipeline_traced(headline, dry_run=True)
    report = format_dry_run_report(traced.final_state, steps=traced.steps)
    for tag in (
        "PIPELINE REPORT",
        "PIPELINE TRACE",
        "ATOMIC FACTS",
        "VERIFIED CAUSAL EDGES",
        "REJECTED HYPOTHESES",
        "SKEPTIC LOG",
        "WEAVER",
    ):
        run.check(f"section [{tag}]", tag in report)

    run.section("11c atomic_facts formatter")

    lines = format_atomic_facts_section(traced.final_state)
    run.check("facts listed", any("ATOMIC FACTS" in ln for ln in lines))
