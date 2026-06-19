"""Neo4j launcher probe tests."""

from pathlib import Path

from deconstructor.neo4j_launcher import probe_neo4j_installation


def test_probe_finds_compose_in_project_root():
    root = Path(__file__).resolve().parents[1]
    probe = probe_neo4j_installation(root)
    assert probe.compose_file is True


def test_ui_heartbeat_expires():
    from deconstructor.neo4j_launcher import (
        HEARTBEAT_STALE_SEC,
        active_ui_tab_count,
        record_ui_heartbeat,
        remove_ui_tab,
    )

    record_ui_heartbeat("tab-a")
    assert active_ui_tab_count() == 1
    remove_ui_tab("tab-a")
    assert active_ui_tab_count() == 0


def test_managed_mark_and_clear():
    from deconstructor.neo4j_launcher import clear_managed, is_managed_neo4j, mark_managed

    mark_managed(method="docker", project_root=Path("."), label="test")
    assert is_managed_neo4j()
    clear_managed()
    assert not is_managed_neo4j()


def test_resolve_desktop_java_home_finds_cache_jre():
    from deconstructor.neo4j_launcher import _resolve_desktop_java_home, find_desktop_dbms_bins

    bins = find_desktop_dbms_bins()
    if not bins:
        return
    java_home = _resolve_desktop_java_home(bins[0])
    if java_home is not None:
        assert (java_home / "bin" / "java.exe").is_file()


def test_managed_mark_close_desktop_flag():
    from deconstructor import neo4j_launcher as nl
    from deconstructor.neo4j_launcher import clear_managed, is_managed_neo4j, mark_managed

    clear_managed()
    mark_managed(method="desktop_dbms", label="stock", close_desktop_window=True)
    assert is_managed_neo4j()
    with nl._managed_lock:
        assert nl._managed is not None
        assert nl._managed.close_desktop_window is True
    clear_managed()


def test_stop_managed_closes_desktop_for_dbms_method(monkeypatch):
    from deconstructor import neo4j_launcher as nl
    from deconstructor.neo4j_launcher import clear_managed, mark_managed, stop_managed_neo4j

    clear_managed()
    closed: list[str] = []

    def _fake_close(*, reason: str) -> bool:
        closed.append(reason)
        return True

    def _fake_stop(_bin: Path) -> bool:
        return True

    monkeypatch.setattr(nl, "_close_neo4j_desktop_app", _fake_close)
    monkeypatch.setattr(nl, "_stop_desktop_dbms", _fake_stop)
    monkeypatch.setattr(nl, "neo4j_is_available", lambda: False)

    mark_managed(method="desktop_dbms", dbms_bin=Path("."), label="stock", close_desktop_window=False)
    stop_managed_neo4j(reason="test")
    assert closed == ["test"]
    clear_managed()


def test_cleanup_desktop_session_without_managed(monkeypatch):
    from deconstructor import neo4j_launcher as nl
    from deconstructor.neo4j_launcher import (
        clear_link_neo4j_ui_session,
        clear_managed,
        maybe_cleanup_if_ui_idle,
        register_link_neo4j_ui_session,
    )

    clear_managed()
    clear_link_neo4j_ui_session()
    nl._desktop_launched_by_link = False
    closed: list[str] = []
    monkeypatch.setattr(nl, "_close_neo4j_desktop_app", lambda *, reason: closed.append(reason) or True)

    register_link_neo4j_ui_session()
    assert maybe_cleanup_if_ui_idle(reason="test_idle") is True
    assert closed == ["test_idle"]
    clear_link_neo4j_ui_session()


def test_maybe_stop_skips_when_tabs_active():
    from deconstructor.neo4j_launcher import (
        clear_managed,
        mark_managed,
        maybe_stop_managed_if_ui_idle,
        record_ui_heartbeat,
        remove_ui_tab,
    )

    clear_managed()
    mark_managed(method="docker", project_root=Path("."), label="t")
    record_ui_heartbeat("tab-x")
    assert maybe_stop_managed_if_ui_idle() is False
    remove_ui_tab("tab-x")
    clear_managed()
