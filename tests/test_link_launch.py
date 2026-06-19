"""link_launch LaunchTracker."""

from link_launch import LaunchTracker, _fetch_status


def test_launch_tracker_fail():
    t = LaunchTracker()
    t.start("L3-HEALTH", "GET /api/status")
    code = t.fail("L3-HEALTH", "empty reply")
    assert code == 1
    assert t.failed_step == "L3-HEALTH"
    assert t.steps[-1].status == "error"


def test_fetch_status_when_server_up():
    kind, data, _ = _fetch_status()
    if kind == "ok":
        assert "neo4j" in data
