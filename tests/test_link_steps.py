"""LinkStepTracker 단위 테스트."""

import io
import sys

from deconstructor.web.link_steps import LinkStepTracker


def test_tracker_start_em_dash_on_cp949_stdout():
    """Windows cp949 콘솔에서 em dash(—) 로그가 분석을 중단하지 않음."""
    buf = io.TextIOWrapper(io.BytesIO(), encoding="cp949", errors="strict")
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        t = LinkStepTracker()
        t.start("S0-PARSE-CTYPE", "Content-Type 확인", "multipart/form-data")
        t.ok("S0-PARSE-CTYPE")
    finally:
        sys.stdout = old_stdout
    assert t.steps[0].status == "ok"


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
