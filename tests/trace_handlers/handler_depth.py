"""Tests for recursion_depth trace handler."""

from deconstructor.pipeline.trace.summarize.handlers.depth import detail_recursion_depth


def test_detail_recursion_depth():
    assert detail_recursion_depth({"recursion_depth": 3}) == "depth->3"


def test_detail_depth_missing():
    assert detail_recursion_depth({}) is None
