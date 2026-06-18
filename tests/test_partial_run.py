"""Tests for partial_run detection (Phase 9)."""

from deconstructor.pipeline.partial_run import (
    REASON_DEPTH_CAP,
    detect_partial_run,
)
from deconstructor.skeptic.run_log import build_skeptic_log
from tests.conftest import fact


def test_not_partial_at_null_floor():
    info = detect_partial_run(
        extracted_facts=[],
        completed_facts=[fact("a", "x", "s -> 1")],
        recursion_depth=2,
        max_recursion_depth=5,
    )
    assert info.partial_run is False
    assert info.reason == ""


def test_partial_at_depth_cap():
    non_atomic = fact("n", "x", "compound -> event", is_atomic=False)
    info = detect_partial_run(
        extracted_facts=[non_atomic],
        completed_facts=[],
        recursion_depth=2,
        max_recursion_depth=2,
    )
    assert info.partial_run is True
    assert info.reason == REASON_DEPTH_CAP
    assert info.non_atomic_count == 1


def test_skeptic_log_partial_warn():
    from deconstructor.pipeline.partial_run import PartialRunInfo

    partial = PartialRunInfo(
        partial_run=True,
        reason=REASON_DEPTH_CAP,
        non_atomic_count=1,
        completed_atomic_count=0,
        recursion_depth=2,
        max_recursion_depth=2,
    )
    log = build_skeptic_log(partial, completed_fact_count=0, ran_batch=False)
    codes = [e.code for e in log]
    assert "PARTIAL_INPUT" in codes
    assert "DEPTH_CAP_TRUNCATION" in codes
    assert "INSUFFICIENT_FACTS" in codes
