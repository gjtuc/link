"""Granular tests for report section formatters."""

from __future__ import annotations

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.pipeline_trace import StepRecord
from deconstructor.report.compose import format_dry_run_report
from deconstructor.report.sections.atomic_facts import format_atomic_facts_section
from deconstructor.report.sections.edges import format_edges_section
from deconstructor.report.sections.footer import format_footer_section
from deconstructor.report.sections.header import format_header_section
from deconstructor.report.sections.partial import format_partial_run_section
from deconstructor.report.sections.rejected import format_rejected_section
from deconstructor.report.sections.remaining import format_remaining_section
from deconstructor.report.sections.skeptic_log import format_skeptic_log_section
from deconstructor.report.sections.status import format_status_line
from deconstructor.report.sections.trace import format_step_trace
from deconstructor.report.sections.weaver import format_weaver_section
from deconstructor.skeptic.run_log import SkepticLogEntry
from deconstructor.skeptic.schemas import CausalClassification, RejectedHypothesis
from deconstructor.weaver.schemas import WeaverResult


def _state(**kw):
    base = {
        "raw_text": "A공장 정전",
        "extracted_facts": [],
        "completed_facts": [],
        "recursion_depth": 2,
        "max_recursion_depth": 5,
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "weaver_result": None,
    }
    base.update(kw)
    return base


def test_header_section():
    lines = format_header_section(_state())
    text = "\n".join(lines)
    assert "PIPELINE REPORT" in text
    assert "A공장 정전" in text
    assert "DEPTH CAP" in text


def test_status_complete():
    assert "COMPLETE" in format_status_line(_state())


def test_status_incomplete_at_cap():
    na = AtomicFact(subject="z", state_change="c -> e", is_atomic=False)
    line = format_status_line(
        _state(extracted_facts=[na], recursion_depth=5, max_recursion_depth=5)
    )
    assert "INCOMPLETE" in line


def test_status_in_progress():
    na = AtomicFact(subject="z", state_change="c -> e", is_atomic=False)
    line = format_status_line(_state(extracted_facts=[na], recursion_depth=1))
    assert "IN PROGRESS" in line


def test_trace_section():
    steps = [
        StepRecord(1, "deconstruct", recursion_depth=1, extracted_count=1),
        StepRecord(2, "verify", completed_count=0),
    ]
    text = format_step_trace(steps)
    assert "PIPELINE TRACE" in text
    assert "deconstruct" in text


def test_atomic_facts_section():
    fact = AtomicFact(subject="grid", state_change="power -> off", is_atomic=True)
    lines = format_atomic_facts_section(_state(completed_facts=[fact]))
    assert any("ATOMIC FACTS" in ln for ln in lines)
    assert any("grid" in ln for ln in lines)


def test_remaining_section_empty():
    lines = format_remaining_section(_state())
    assert any("REMAINING" in ln for ln in lines)
    assert any("none" in ln for ln in lines)


def test_remaining_section_shows_leftovers():
    na = AtomicFact(subject="x", state_change="a -> b", is_atomic=False)
    lines = format_remaining_section(_state(extracted_facts=[na]))
    assert any("REMAINING" in ln for ln in lines)


def test_edges_section():
    f1 = AtomicFact(id="a", subject="x", state_change="s -> 1", is_atomic=True)
    f2 = AtomicFact(id="b", subject="y", state_change="s -> 2", is_atomic=True)
    edge = CausalEdge(source_fact_id="a", target_fact_id="b", probability=0.9)
    lines = format_edges_section(_state(verified_edges=[edge]))
    assert any("VERIFIED CAUSAL EDGES" in ln for ln in lines)


def test_rejected_section():
    rej = RejectedHypothesis(
        source_fact_id="a",
        target_fact_id="b",
        classification=CausalClassification.CORRELATION,
        failed_rule_ids=["R01"],
        reason="test",
    )
    lines = format_rejected_section(_state(rejected_hypotheses=[rej]))
    assert any("REJECTED" in ln for ln in lines)


def test_skeptic_log_section():
    entry = SkepticLogEntry(level="INFO", code="TEST", message="ok")
    lines = format_skeptic_log_section(_state(skeptic_log=[entry]))
    assert any("SKEPTIC LOG" in ln for ln in lines)


def test_partial_section_only_when_flagged():
    assert format_partial_run_section(_state()) == []
    lines = format_partial_run_section(
        _state(partial_run=True, partial_run_reason="depth_cap_non_atomic_remain")
    )
    assert lines and "PARTIAL RUN" in "\n".join(lines)


def test_weaver_section():
    wr = WeaverResult(
        mode="console",
        nodes_written=2,
        edges_written=1,
        partial_run=False,
    )
    lines = format_weaver_section(_state(weaver_result=wr))
    assert any("WEAVER" in ln for ln in lines)


def test_footer_section():
    lines = format_footer_section(_state())
    assert lines
    assert any("PIPELINE" in ln or "DRY-RUN" in ln for ln in lines)


def test_compose_includes_all_sections():
    f = AtomicFact(subject="g", state_change="p -> o", is_atomic=True)
    report = format_dry_run_report(
        _state(
            completed_facts=[f],
            verified_edges=[
                CausalEdge(source_fact_id=f.id, target_fact_id="b", probability=0.5)
            ],
        ),
        steps=[StepRecord(1, "deconstruct")],
    )
    for tag in (
        "PIPELINE REPORT",
        "PIPELINE TRACE",
        "ATOMIC FACTS",
        "VERIFIED CAUSAL EDGES",
        "SKEPTIC LOG",
        "WEAVER",
    ):
        assert tag in report
