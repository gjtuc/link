"""LinkStepTracker 단위 테스트."""

from deconstructor.web.link_steps import LinkStepTracker


def test_tracker_ok_and_fail():
    t = LinkStepTracker()
    t.start("S1-INPUT", "입력", "2건")
    t.ok("S1-INPUT")
    t.start("S4-PIPELINE-1", "파이프라인")
    try:
        raise ValueError("SSL verify failed")
    except ValueError as exc:
        out = t.fail(exc)
    assert out["ok"] is False
    assert out["failed_step"] == "S4-PIPELINE-1"
    assert len(out["steps"]) == 2
    assert out["steps"][0]["status"] == "ok"
    assert out["steps"][1]["status"] == "error"
