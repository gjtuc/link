"""
Sprint 7 — watch / guards (SP7-TEST-01).

See ``docs/design/SPRINT-7-watch-spec.md``.
"""

from __future__ import annotations

from deconstructor.guards.batch_warnings import (
    build_watch_report,
    collect_ng2_warnings,
    collect_partial_run_warnings,
)
from deconstructor.guards.ingest_guard import check_f0_a2_blocking, detect_f0_a2_violations
from deconstructor.web.extract import ExtractedSource


def _src(text: str, *, pages: int = 0, label: str = "paper.pdf") -> ExtractedSource:
    return ExtractedSource(
        kind="document",
        label=label,
        text=text,
        source_file=label,
        document_page_count=pages,
    )


def test_sp7_ing02_f0_a2_violation_detected():
    sources = [
        _src("tiny", pages=4, label="scan.pdf"),
        _src("", pages=4, label="scan.pdf"),
    ]
    v = detect_f0_a2_violations(sources)
    assert len(v) == 1
    assert v[0]["code"] == "F0-A2"
    assert v[0]["page_count"] == 4


def test_sp7_ing02_no_violation_enough_chars():
    sources = [_src("x" * 600, pages=5)]
    assert detect_f0_a2_violations(sources) == []


def test_sp7_ing03_blocking_result():
    guard = check_f0_a2_blocking([_src("ab", pages=10)])
    assert guard.blocking is True
    assert "F0-A2" in guard.message


def test_sp7_dec01_partial_run_warning():
    states = [
        {
            "partial_run": True,
            "partial_run_reason": "depth_cap_non_atomic_remain",
            "source_document_meta": {"source_file": "a.txt"},
        }
    ]
    w = collect_partial_run_warnings(states)
    assert len(w) == 1
    assert w[0]["code"] == "PARTIAL_RUN"


def test_sp7_skp01_ng2_many_nodes_no_skeleton_signal():
    sk = {"gap_count": 0, "strong_chain_count": 0, "weak_count": 0}
    w = collect_ng2_warnings(node_count=25, skeleton=sk)
    assert len(w) == 1
    assert w[0]["code"] == "NG-2"
    assert "Gap/Strong" in w[0]["message"]


def test_sp7_skp01_no_ng2_when_gap_present():
    sk = {"gap_count": 2, "strong_chain_count": 0}
    assert collect_ng2_warnings(node_count=30, skeleton=sk) == []


def test_sp7_api01_watch_report_keys():
    watch = build_watch_report(
        pipeline_states=[{"partial_run": False}],
        skeleton={"gap_count": 1, "strong_chain_count": 0},
        node_count=5,
    )
    assert "warnings" in watch
    assert watch["has_partial_run"] is False
    assert watch["warning_count"] >= 0
