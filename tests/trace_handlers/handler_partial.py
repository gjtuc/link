"""Tests for partial_run trace handler."""

from deconstructor.pipeline.trace.summarize.handlers.partial import detail_partial_run


def test_detail_partial_run_true():
    assert detail_partial_run({"partial_run": True}) == "partial_run=True"


def test_detail_partial_missing():
    assert detail_partial_run({}) is None
