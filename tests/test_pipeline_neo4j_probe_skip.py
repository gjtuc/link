"""μ-PROBE-S5 — LINK_DISABLE_NEO4J_AUTO_START contract (offline)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.pipeline_batch import _ensure_neo4j_tracked


@pytest.mark.parametrize("env_val", ("1", "true", "YES"))
def test_s5_skips_auto_start_when_env_set(monkeypatch, env_val: str):
    monkeypatch.setenv("LINK_DISABLE_NEO4J_AUTO_START", env_val)
    tracker = LinkStepTracker()
    with patch("deconstructor.neo4j_launcher.ensure_neo4j_running") as mock_ensure:
        use_db, sync = _ensure_neo4j_tracked(tracker, [])
    mock_ensure.assert_not_called()
    assert use_db is False
    assert sync is not None
    assert sync["message"] == "LINK_DISABLE_NEO4J_AUTO_START"
    assert sync["method"] == "disabled"
    steps = tracker.to_list()
    assert any(
        s["step"] == "S5-NEO4J-ENSURE"
        and s["status"] == "skip"
        and "auto-start disabled" in s["label"]
        for s in steps
    )


def test_s5_may_call_ensure_when_env_unset(monkeypatch):
    monkeypatch.delenv("LINK_DISABLE_NEO4J_AUTO_START", raising=False)
    tracker = LinkStepTracker()
    with (
        patch("deconstructor.viz.neo4j_utils.neo4j_is_available", return_value=False),
        patch(
            "deconstructor.neo4j_launcher.probe_neo4j_installation",
        ) as mock_probe,
        patch(
            "deconstructor.neo4j_launcher.ensure_neo4j_running",
        ) as mock_ensure,
    ):
        mock_probe.return_value = type(
            "Probe",
            (),
            {"any_installed": True, "docker_cli": False, "desktop_exe": True},
        )()
        mock_ensure.return_value = type(
            "Ensure",
            (),
            {
                "available": False,
                "method": "desktop",
                "message": "timeout",
                "waited_sec": 90.0,
            },
        )()
        use_db, _ = _ensure_neo4j_tracked(tracker, [])
    mock_ensure.assert_called_once()
    assert use_db is False
