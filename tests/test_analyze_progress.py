"""analyze_progress — 완료 단계 가중치만 반영 (시간 보간 없음)."""

from deconstructor.web.analyze_progress import (
    compute_percent_from_steps,
    snapshot,
    sync_tracker,
)
from deconstructor.web.link_steps import LinkStepRecord, LinkStepTracker


def test_compute_percent_empty():
    pct, label, _phase = compute_percent_from_steps([], source_count=1)
    assert pct == 0
    assert "시작" in label


def test_compute_percent_grows_with_ok_steps():
    steps = [
        LinkStepRecord(step="S0-A", label="파싱", status="ok"),
        LinkStepRecord(step="S4-1-NODE-deconstruct", label="Deconstruct", status="ok"),
        LinkStepRecord(step="S4-1-NODE-deconstruct-LLM", label="LLM", status="running"),
    ]
    pct, label, _ = compute_percent_from_steps(steps, source_count=1)
    assert pct > 0
    assert "LLM" in label


def test_running_step_does_not_creep_over_time():
    import time

    started = time.time() - 30.0
    at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(started)) + "+00:00"
    steps = [
        LinkStepRecord(step="S0-A", label="파싱", status="ok"),
        LinkStepRecord(
            step="S4-1-NODE-deconstruct-LLM",
            label="Deconstruct LLM",
            status="running",
            at=at,
        ),
    ]
    pct_early, _, _ = compute_percent_from_steps(steps, source_count=1)
    pct_late, _, _ = compute_percent_from_steps(steps, source_count=1)
    assert pct_early == pct_late


def test_snapshot_updates_when_step_completes():
    from deconstructor.web.analyze_progress import begin_job, clear_job

    begin_job(source_count=1)
    tr = LinkStepTracker()
    sync_tracker(tr)
    tr.start("S4-1-NODE-deconstruct-LLM", "LLM", "live")
    sync_tracker(tr)
    snap1 = snapshot()
    tr.ok("S4-1-NODE-deconstruct-LLM", "done")
    sync_tracker(tr)
    snap2 = snapshot()
    clear_job()
    assert snap2["percent"] > snap1["percent"]


def test_tracker_on_change_fires():
    seen = []

    def on_change(tr: LinkStepTracker) -> None:
        seen.append(len(tr.steps))

    tr = LinkStepTracker(on_change=on_change)
    tr.start("S1", "test")
    tr.ok("S1")
    assert seen == [1, 1]
