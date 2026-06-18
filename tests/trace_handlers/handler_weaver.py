"""Tests for weaver_result trace handler."""

from deconstructor.pipeline.trace.summarize.handlers.weaver import detail_weaver_result
from deconstructor.weaver.schemas import WeaverResult


def test_detail_weaver_result():
    wr = WeaverResult(mode="console", nodes_written=2, edges_written=1)
    assert detail_weaver_result({"weaver_result": wr}) == (
        "weaver=console nodes=2 edges=1"
    )


def test_detail_weaver_none():
    assert detail_weaver_result({"weaver_result": None}) is None
    assert detail_weaver_result({}) is None
