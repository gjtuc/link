"""
Neo4j 설치 감지 및 자동 기동/종료 (Docker / Neo4j Desktop dbms)
================================================================

Link UI 세션 종료 시:
  - Link가 켠 DB는 stop 시도
  - **Link가 연 Neo4j Desktop 창은 닫음** (DB STOPPED 여부와 무관)

세션 추적 (2026-06)
-------------------
  ``register_link_neo4j_ui_session`` — Desktop 실행·managed 기동 시 등록.
  managed 없이 Desktop만 띄운 경우(neo4j.bat 실패 → Desktop.exe)도
  UI idle 시 ``maybe_cleanup_if_ui_idle`` 이 창을 닫음.

사용자가 분석 전부터 Desktop을 직접 켜 둔 경우(``already_running``)는 창을 건드리지 않음.
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from deconstructor.viz.neo4j_utils import neo4j_is_available

logger = logging.getLogger(__name__)

DEFAULT_WAIT_SEC = 90
POLL_INTERVAL_SEC = 2.0

HEARTBEAT_STALE_SEC = 35.0
WATCHDOG_POLL_SEC = 10.0
HIDDEN_TAB_BYE_SEC = 45.0

_managed_lock = threading.Lock()
_managed: "ManagedNeo4j | None" = None
_tab_heartbeats: dict[str, float] = {}
_heartbeat_lock = threading.Lock()
_watchdog_started = False
_desktop_proc: subprocess.Popen | None = None
_desktop_launched_by_link = False
_link_neo4j_ui_session = False


@dataclass(frozen=True)
class Neo4jInstallProbe:
    """이 PC에서 자동 기동 가능한 Neo4j 경로."""

    docker_cli: bool
    compose_file: bool
    desktop_exe: Path | None
    desktop_dbms: list[Path]

    @property
    def any_installed(self) -> bool:
        return (
            (self.docker_cli and self.compose_file)
            or bool(self.desktop_dbms)
            or self.desktop_exe is not None
        )


@dataclass(frozen=True)
class Neo4jEnsureResult:
    available: bool
    method: str
    message: str
    waited_sec: float = 0.0


@dataclass(frozen=True)
class ManagedNeo4j:
    """Link가 직접 기동한 Neo4j (종료 대상)."""

    method: str  # docker | desktop_dbms
    project_root: Path | None = None
    dbms_bin: Path | None = None
    label: str = ""
    close_desktop_window: bool = False


def is_managed_neo4j() -> bool:
    with _managed_lock:
        return _managed is not None


def link_neo4j_ui_session_active() -> bool:
    """Link가 이번 서버 실행에서 Desktop을 띄웠거나 managed Neo4j 세션을 연 경우."""
    return _link_neo4j_ui_session or _desktop_launched_by_link or is_managed_neo4j()


def register_link_neo4j_ui_session() -> None:
    """분석·자동 기동으로 Neo4j Desktop/DB 세션이 열렸음 — UI idle 시 정리 대상."""
    global _link_neo4j_ui_session
    _link_neo4j_ui_session = True
    _log("registered link neo4j ui session (idle 시 Desktop·DB 정리)")


def clear_link_neo4j_ui_session() -> None:
    global _link_neo4j_ui_session
    _link_neo4j_ui_session = False


def mark_managed(
    *,
    method: str,
    project_root: Path | None = None,
    dbms_bin: Path | None = None,
    label: str = "",
    close_desktop_window: bool = False,
) -> None:
    global _managed
    with _managed_lock:
        _managed = ManagedNeo4j(
            method=method,
            project_root=project_root,
            dbms_bin=dbms_bin,
            label=label,
            close_desktop_window=close_desktop_window,
        )
    _log(
        f"marked managed neo4j method={method} label={label or '-'} "
        f"close_desktop={close_desktop_window}"
    )
    register_link_neo4j_ui_session()


def clear_managed() -> None:
    global _managed
    with _managed_lock:
        _managed = None


def record_ui_heartbeat(tab_id: str) -> None:
    if not tab_id:
        return
    with _heartbeat_lock:
        _tab_heartbeats[tab_id] = time.monotonic()


def remove_ui_tab(tab_id: str) -> None:
    if not tab_id:
        return
    with _heartbeat_lock:
        _tab_heartbeats.pop(tab_id, None)


def active_ui_tab_count() -> int:
    now = time.monotonic()
    with _heartbeat_lock:
        stale = [tid for tid, ts in _tab_heartbeats.items() if now - ts > HEARTBEAT_STALE_SEC]
        for tid in stale:
            del _tab_heartbeats[tid]
        return len(_tab_heartbeats)


def maybe_stop_managed_if_ui_idle(*, reason: str = "no_ui_tabs") -> bool:
    """브라우저 UI idle 시 managed Neo4j stop + Link가 연 Desktop 창 닫기."""
    return maybe_cleanup_if_ui_idle(reason=reason)


def maybe_cleanup_if_ui_idle(*, reason: str = "no_ui_tabs") -> bool:
    if active_ui_tab_count() > 0:
        return False
    if is_managed_neo4j():
        return stop_managed_neo4j(reason=reason)
    if _link_neo4j_ui_session or _desktop_launched_by_link:
        _log(f"cleanup link neo4j ui session ({reason}) — managed 없음, Desktop만 닫기")
        _close_neo4j_desktop_app(reason=reason)
        clear_link_neo4j_ui_session()
        return True
    return False


def _cleanup_on_process_exit() -> None:
    if is_managed_neo4j():
        stop_managed_neo4j(reason="ui_server_exit")
    elif _link_neo4j_ui_session or _desktop_launched_by_link:
        _close_neo4j_desktop_app(reason="ui_server_exit")
        clear_link_neo4j_ui_session()


def stop_managed_neo4j(*, reason: str = "shutdown") -> bool:
    """Link가 켠 Neo4j 중지 + (Desktop 세션이면) Neo4j Desktop 창 닫기."""
    with _managed_lock:
        target = _managed
    if target is None:
        return False

    _log(f"stop managed neo4j ({reason}) method={target.method}")
    ok = False
    if target.method == "docker" and target.project_root:
        ok = _stop_docker_compose(target.project_root)
    elif target.method == "desktop_dbms" and target.dbms_bin:
        ok = _stop_desktop_dbms(target.dbms_bin)

    # desktop_dbms: Link가 neo4j.bat 으로 기동한 세션 — DB stop 후 Desktop GUI도 닫음
    if (
        target.method == "desktop_dbms"
        or target.close_desktop_window
        or _desktop_launched_by_link
    ):
        _close_neo4j_desktop_app(reason=reason)

    if ok or not neo4j_is_available():
        clear_managed()
        _log("managed neo4j cleared")
        return True

    _log("neo4j still reachable after stop attempt — managed flag kept")
    return ok


def _watchdog_loop() -> None:
    while True:
        time.sleep(WATCHDOG_POLL_SEC)
        maybe_cleanup_if_ui_idle(reason="watchdog_no_ui_tabs")


def start_ui_watchdog() -> None:
    global _watchdog_started
    if _watchdog_started:
        return
    _watchdog_started = True
    thread = threading.Thread(target=_watchdog_loop, name="neo4j-ui-watchdog", daemon=True)
    thread.start()
    atexit.register(_cleanup_on_process_exit)


def _log(msg: str) -> None:
    line = f"[Neo4jLauncher] {msg}"
    logger.info(line)
    print(line)


def _desktop_exe_candidates() -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    pf = Path(os.environ.get("ProgramFiles", ""))
    pf86 = Path(os.environ.get("ProgramFiles(x86)", ""))
    return [
        pf / "Neo4j Desktop 2" / "Neo4j Desktop 2.exe",
        pf86 / "Neo4j Desktop 2" / "Neo4j Desktop 2.exe",
        pf / "Neo4j Desktop" / "Neo4j Desktop.exe",
        local / "Programs" / "Neo4j Desktop" / "Neo4j Desktop.exe",
        local / "Neo4j Desktop" / "Neo4j Desktop.exe",
    ]


def _desktop_data_roots() -> list[Path]:
    home = Path.home()
    return [
        home / ".Neo4jDesktop2",
        home / ".Neo4jDesktop",
        Path(os.environ.get("APPDATA", "")) / "Neo4j",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Neo4j",
    ]


def _dbms_display_name(dbms_bin: Path) -> str:
    meta = dbms_bin.parent / "relate.dbms.json"
    if not meta.is_file():
        return dbms_bin.parent.name
    try:
        payload = json.loads(meta.read_text(encoding="utf-8"))
        return str(payload.get("name") or dbms_bin.parent.name)
    except (OSError, json.JSONDecodeError, TypeError):
        return dbms_bin.parent.name


def find_desktop_dbms_bins() -> list[Path]:
    """Neo4j Desktop(1·2)이 설치한 dbms ``bin`` 폴더 — Cache 템플릿 제외."""
    bins: list[Path] = []
    seen: set[str] = set()
    for root in _desktop_data_roots():
        if not root.is_dir():
            continue
        for bat in root.rglob("neo4j.bat"):
            if "dbmss" not in bat.parts:
                continue
            if "Cache" in bat.parts:
                continue
            key = str(bat.parent.resolve())
            if key in seen:
                continue
            seen.add(key)
            bins.append(bat.parent)

    def _sort_key(bin_dir: Path) -> tuple:
        name = _dbms_display_name(bin_dir).lower()
        # link 프로젝트 DB 우선, 그다음 실제 Data/dbms
        link_first = 0 if name == "link" else 1
        in_data = 0 if "Data" in bin_dir.parts else 1
        return (link_first, in_data, name, str(bin_dir))

    bins.sort(key=_sort_key)
    return bins


def probe_neo4j_installation(project_root: Path | None = None) -> Neo4jInstallProbe:
    root = project_root or Path.cwd()
    compose = (root / "docker-compose.yml").is_file()
    docker_cli = shutil.which("docker") is not None
    desktop_exe = next((p for p in _desktop_exe_candidates() if p.is_file()), None)
    dbms = find_desktop_dbms_bins()
    return Neo4jInstallProbe(
        docker_cli=docker_cli,
        compose_file=compose,
        desktop_exe=desktop_exe,
        desktop_dbms=dbms,
    )


def wait_for_neo4j(timeout_sec: float = DEFAULT_WAIT_SEC) -> bool:
    if neo4j_is_available():
        return True
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SEC)
        if neo4j_is_available():
            return True
    return neo4j_is_available()


def _start_docker_compose(project_root: Path) -> bool:
    compose = project_root / "docker-compose.yml"
    if not compose.is_file() or shutil.which("docker") is None:
        return False
    _log(f"docker compose up -d ({project_root})")
    try:
        proc = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"docker compose failed: {exc}")
        return False
    if proc.returncode != 0:
        _log(f"docker compose exit {proc.returncode}: {proc.stderr.strip()[:200]}")
        return False
    return True


def _resolve_desktop_java_home(bin_dir: Path) -> Path | None:
    """Neo4j Desktop 2 dbms — neo4j.bat 이 Cache/runtime JRE 를 못 찾을 때 보조."""
    for root in _desktop_data_roots():
        runtime = root / "Cache" / "runtime"
        if not runtime.is_dir():
            continue
        candidates = sorted(
            (p for p in runtime.iterdir() if p.is_dir() and "jre" in p.name.lower()),
            key=lambda p: p.name,
            reverse=True,
        )
        for jre in candidates:
            java_exe = jre / "bin" / "java.exe"
            if java_exe.is_file():
                return jre
    return None


def _neo4j_subprocess_env(bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    java_home = _resolve_desktop_java_home(bin_dir)
    if java_home:
        env["JAVA_HOME"] = str(java_home)
        env["PATH"] = f"{java_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    return env


def _start_desktop_dbms(bin_dir: Path) -> bool:
    neo4j_bat = bin_dir / "neo4j.bat"
    if not neo4j_bat.is_file():
        return False
    _log(f"neo4j start → {bin_dir}")
    try:
        proc = subprocess.run(
            [str(neo4j_bat), "start"],
            cwd=str(bin_dir),
            env=_neo4j_subprocess_env(bin_dir),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"neo4j start failed: {exc}")
        return False
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:200]
        _log(f"neo4j start exit {proc.returncode}: {err}")
        return False
    return True


def _stop_docker_compose(project_root: Path) -> bool:
    if shutil.which("docker") is None:
        return False
    _log(f"docker compose stop ({project_root})")
    try:
        proc = subprocess.run(
            ["docker", "compose", "stop"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"docker compose stop failed: {exc}")
        return False
    if proc.returncode != 0:
        _log(f"docker compose stop exit {proc.returncode}: {(proc.stderr or '')[:200]}")
        return False
    return True


def _stop_desktop_dbms(bin_dir: Path) -> bool:
    neo4j_bat = bin_dir / "neo4j.bat"
    if not neo4j_bat.is_file():
        return False
    _log(f"neo4j stop → {bin_dir}")
    try:
        proc = subprocess.run(
            [str(neo4j_bat), "stop"],
            cwd=str(bin_dir),
            env=_neo4j_subprocess_env(bin_dir),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"neo4j stop failed: {exc}")
        return False
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:200]
        _log(f"neo4j stop exit {proc.returncode}: {err}")
        return False
    return True


def _launch_desktop_app(exe: Path) -> None:
    global _desktop_proc, _desktop_launched_by_link
    _log(f"Neo4j Desktop 실행 → {exe}")
    try:
        _desktop_proc = subprocess.Popen(
            [str(exe)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _desktop_launched_by_link = True
        register_link_neo4j_ui_session()
    except OSError as exc:
        _log(f"Desktop launch failed: {exc}")


def _close_neo4j_desktop_app(*, reason: str) -> bool:
    """Neo4j Desktop 앱 창 종료 (Electron). DB STOPPED 여부와 무관."""
    global _desktop_proc, _desktop_launched_by_link
    _log(f"close Neo4j Desktop window ({reason})")
    closed = False

    if _desktop_proc is not None and _desktop_proc.poll() is None:
        try:
            _desktop_proc.terminate()
            _desktop_proc.wait(timeout=5)
            closed = True
        except subprocess.TimeoutExpired:
            _desktop_proc.kill()
            closed = True
        except OSError as exc:
            _log(f"desktop proc terminate failed: {exc}")
        finally:
            _desktop_proc = None

    if os.name == "nt":
        images = ("Neo4j Desktop 2.exe", "Neo4j Desktop.exe")
        for attempt in (1, 2):
            for image in images:
                try:
                    proc = subprocess.run(
                        ["taskkill", "/IM", image, "/T", "/F"],
                        capture_output=True,
                        text=True,
                        timeout=20,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    _log(f"taskkill {image} failed: {exc}")
                    continue
                if proc.returncode == 0:
                    _log(f"taskkill ok: {image} (attempt {attempt})")
                    closed = True
                elif proc.returncode == 128:
                    _log(f"taskkill: {image} not running")
                else:
                    err = (proc.stderr or proc.stdout or "").strip()[:120]
                    _log(f"taskkill {image} exit {proc.returncode}: {err}")
            if closed:
                break
            time.sleep(1.5)

    _desktop_launched_by_link = False
    clear_link_neo4j_ui_session()
    return closed


def ensure_neo4j_running(
    project_root: Path | None = None,
    *,
    wait_timeout_sec: float = DEFAULT_WAIT_SEC,
) -> Neo4jEnsureResult:
    """
    Bolt 연결 가능할 때까지 설치된 경로로 Neo4j 기동 시도.

    Returns:
        Neo4jEnsureResult — available=True 면 Bolt+인증 OK.
    """
    root = (project_root or Path.cwd()).resolve()
    t0 = time.monotonic()
    was_available_at_start = neo4j_is_available()

    if was_available_at_start:
        return Neo4jEnsureResult(
            available=True,
            method="already_running",
            message=(
                "Neo4j 이미 연결됨 (분석 전부터 켜 둔 DB — Link가 stop·Desktop 닫기 안 함. "
                "탭만 닫아도 Desktop은 유지됨)"
            ),
        )

    probe = probe_neo4j_installation(root)
    if not probe.any_installed:
        return Neo4jEnsureResult(
            available=False,
            method="none",
            message="Neo4j/Docker 미설치 — Docker Desktop 또는 Neo4j Desktop 설치 후 link_docker_up.bat 참고",
            waited_sec=time.monotonic() - t0,
        )

    started_method = ""

    if probe.docker_cli and probe.compose_file:
        if _start_docker_compose(root):
            started_method = "docker"
            if wait_for_neo4j(wait_timeout_sec):
                mark_managed(method="docker", project_root=root, label="docker")
                return Neo4jEnsureResult(
                    available=True,
                    method="docker",
                    message="Docker Neo4j 기동·연결 완료",
                    waited_sec=time.monotonic() - t0,
                )

    for bin_dir in probe.desktop_dbms:
        if _start_desktop_dbms(bin_dir):
            started_method = "desktop_dbms"
            label = _dbms_display_name(bin_dir)
            if wait_for_neo4j(min(wait_timeout_sec, 60)):
                mark_managed(method="desktop_dbms", dbms_bin=bin_dir, label=label, close_desktop_window=True)
                return Neo4jEnsureResult(
                    available=True,
                    method="desktop_dbms",
                    message=f"Neo4j Desktop DB 「{label}」 기동·연결 완료",
                    waited_sec=time.monotonic() - t0,
                )

    if probe.desktop_exe:
        _launch_desktop_app(probe.desktop_exe)
        if wait_for_neo4j(60):
            if probe.desktop_dbms and not was_available_at_start:
                bin_dir = probe.desktop_dbms[0]
                mark_managed(
                    method="desktop_dbms",
                    dbms_bin=bin_dir,
                    label=_dbms_display_name(bin_dir),
                    close_desktop_window=True,
                )
            return Neo4jEnsureResult(
                available=True,
                method="desktop_app",
                message="Neo4j Desktop 실행 후 DB 연결됨 — 탭을 닫으면 Link가 stop 시도",
                waited_sec=time.monotonic() - t0,
            )

    if probe.docker_cli and probe.compose_file:
        hint = "Docker는 떴을 수 있으나 비밀번호 불일치 — local_settings NEO4J_PASSWORD 와 docker-compose NEO4J_AUTH 확인"
    elif probe.desktop_exe:
        names = [_dbms_display_name(b) for b in probe.desktop_dbms]
        db_hint = f" (DB: {', '.join(names)})" if names else ""
        hint = f"Neo4j Desktop 2에서 DB를 Start 하세요{db_hint}. local_settings NEO4J_PASSWORD 확인"
    else:
        hint = "Neo4j 설치 경로를 찾지 못했습니다"

    return Neo4jEnsureResult(
        available=neo4j_is_available(),
        method=started_method or "failed",
        message=hint if not neo4j_is_available() else "Neo4j 연결됨",
        waited_sec=time.monotonic() - t0,
    )


def persist_state_to_neo4j(state: dict) -> None:
    """이미 계산된 파이프라인 state 를 Neo4j에만 저장 (LLM 재호출 없음)."""
    from deconstructor.weaver.node import weaver_node

    weaver_node(state, persist_db=True)
