"""Tests for summarize compose (handler registry integration)."""

from deconstructor.pipeline.trace.summarize.compose import summarize_update
from deconstructor.weaver.schemas import WeaverResult


def test_summarize_update_composes_multiple_handlers():
    wr = WeaverResult(mode="console", nodes_written=2, edges_written=1)
    record = summarize_update(
        "weaver",
        {"weaver_result": wr, "recursion_depth": 2, "partial_run": False},
    )
    assert record.node == "weaver"
    assert "weaver=console" in record.detail
    assert "depth->2" in record.detail
    assert "partial_run=False" in record.detail
    assert record.recursion_depth == 2


def test_summarize_update_empty_update():
    record = summarize_update("verify", {})
    assert record.node == "verify"
    assert record.detail == ""
