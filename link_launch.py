"""
Link UI 부트스트랩 — 단계 코드(L*)로 서버 기동·헬스체크·브라우저 열기
====================================================================

``link_ui.bat`` → 이 스크립트. Windows ``start`` 따옴표 버그(\\\\ 경고창) 회피.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "link_launch.log"
HOST = "127.0.0.1"
PORT = 8765
BASE = f"http://{HOST}:{PORT}"
STATUS_URL = f"{BASE}/api/status"
PROGRESS_URL = f"{BASE}/api/analyze/progress"
REQUIRED_FEATURES = frozenset({"analyze_progress", "analyze_async"})
HEALTH_WAIT_SEC = 45
HEALTH_INTERVAL_SEC = 1.0


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


@dataclass
class LaunchStep:
    step: str
    label: str
    status: str  # running | ok | error | skip
    detail: str = ""
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LaunchTracker:
    def __init__(self) -> None:
        self.steps: list[LaunchStep] = []
        self.failed_step: str | None = None
        self._current: str | None = None

    def start(self, step: str, label: str, detail: str = "") -> None:
        self._current = step
        self.steps.append(LaunchStep(step, label, "running", detail))
        line = f"[LinkLaunch:{step}] {label}"
        if detail:
            line += f" - {detail}"
        try:
            _safe_print(line)
        except Exception:
            pass
        self._flush_log()

    def ok(self, step: str | None = None, detail: str = "") -> None:
        code = step or self._current
        if not code:
            return
        for rec in reversed(self.steps):
            if rec.step == code and rec.status == "running":
                rec.status = "ok"
                if detail:
                    rec.detail = detail
                _safe_print(f"[LinkLaunch:{code}] OK {detail}".rstrip())
                self._flush_log()
                return

    def skip(self, step: str, label: str, detail: str = "") -> None:
        self.steps.append(LaunchStep(step, label, "skip", detail))
        _safe_print(f"[LinkLaunch:{step}] SKIP {label} {detail}".rstrip())
        self._flush_log()

    def fail(self, step: str, message: str) -> int:
        self.failed_step = step
        for rec in reversed(self.steps):
            if rec.step == step and rec.status == "running":
                rec.status = "error"
                rec.detail = message[:500]
                break
        else:
            self.steps.append(LaunchStep(step, "오류", "error", message[:500]))
        _safe_print(f"[LinkLaunch:{step}] ERROR {message}")
        self._flush_log()
        return 1

    def to_list(self) -> list[dict[str, str]]:
        return [
            {
                "step": s.step,
                "label": s.label,
                "status": s.status,
                "detail": s.detail,
                "at": s.at,
            }
            for s in self.steps
        ]

    def _flush_log(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "failed_step": self.failed_step,
            "steps": self.to_list(),
        }
        LOG_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _venv_python() -> Path:
    return ROOT / "venv" / "Scripts" / "python.exe"


def _port_pids() -> list[int]:
    """8765 포트 LISTEN 중인 PID 목록 (Windows netstat)."""
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"],
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    pids: list[int] = []
    token = f"{HOST}:{PORT}"
    for line in out.splitlines():
        if "LISTENING" not in line or token not in line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid not in pids:
            pids.append(pid)
    return pids


def _probe_socket() -> tuple[bool, str]:
    try:
        with socket.create_connection((HOST, PORT), timeout=2):
            return True, "tcp open"
    except OSError as exc:
        return False, str(exc)


def _status_has_required_features(data: dict) -> tuple[bool, str]:
    link = data.get("link_ui")
    if not isinstance(link, dict):
        return False, "link_ui 메타 없음 (구 서버)"
    features = set(link.get("features") or [])
    missing = REQUIRED_FEATURES - features
    if missing:
        return False, f"기능 부족: {', '.join(sorted(missing))}"
    return True, f"link_ui {link.get('version', '?')}"


def _fetch_progress() -> tuple[bool, str]:
    req = urllib.request.Request(PROGRESS_URL, headers={"User-Agent": "LinkLaunch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status != 200:
                return False, f"/api/analyze/progress HTTP {resp.status}"
            return True, "progress api ok"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, "/api/analyze/progress 404 (구 서버 — 재시작 필요)"
        return False, f"/api/analyze/progress HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def _existing_server_ready() -> tuple[bool, str]:
    kind, data, detail = _fetch_status()
    if kind != "ok" or data is None:
        return False, detail
    feat_ok, feat_detail = _status_has_required_features(data)
    if not feat_ok:
        return False, feat_detail
    prog_ok, prog_detail = _fetch_progress()
    if not prog_ok:
        return False, prog_detail
    return True, f"{detail}; {feat_detail}; {prog_detail}"


def _fetch_status() -> tuple[str, dict | None, str]:
    """
    Returns (kind, data, detail)
    kind: ok | empty | http_error | network
    """
    req = urllib.request.Request(STATUS_URL, headers={"User-Agent": "LinkLaunch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body.strip():
                return "empty", None, "body length 0 (ERR_EMPTY_RESPONSE)"
            try:
                data = json.loads(body)
            except json.JSONDecodeError as exc:
                return "http_error", None, f"JSON parse: {exc}; body={body[:120]!r}"
            return "ok", data, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return "http_error", None, f"HTTP {exc.code} {exc.reason}"
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if "Remote end closed" in str(reason) or "empty" in str(reason).lower():
            return "empty", None, str(reason)
        return "network", None, str(reason)
    except Exception as exc:
        return "network", None, str(exc)


def _kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            check=False,
            capture_output=True,
            timeout=15,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _spawn_server(python: Path, tracker: LaunchTracker) -> subprocess.Popen | None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    server_log = LOG_DIR / "link_ui.log"
    tracker.start("L4-SPAWN-LOG", "서버 로그 파일", str(server_log.name))
    log_fp = open(server_log, "a", encoding="utf-8")
    log_fp.write(f"\n[{datetime.now().isoformat()}] link_launch spawn\n")
    log_fp.flush()
    tracker.ok("L4-SPAWN-LOG")

    tracker.start("L4-SPAWN-PROC", "python -m deconstructor.web.server")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    creationflags = 0
    if sys.platform == "win32":
        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        creationflags = create_no_window
    try:
        proc = subprocess.Popen(
            [str(python), "-m", "deconstructor.web.server"],
            cwd=str(ROOT),
            env=env,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except OSError as exc:
        tracker.fail("L4-SPAWN-PROC", str(exc))
        log_fp.close()
        return None
    tracker.ok("L4-SPAWN-PROC", f"pid={proc.pid}")
    return proc


def _open_browser(tracker: LaunchTracker) -> None:
    tracker.start("L6-BROWSER-FIND", "Chrome 경로 탐색")
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LocalAppData", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    chrome = next((p for p in candidates if p.is_file()), None)
    tracker.ok("L6-BROWSER-FIND", str(chrome.name) if chrome else "default")

    url = f"{BASE}/"
    tracker.start("L6-BROWSER-OPEN", "브라우저 열기", url)
    if chrome:
        subprocess.Popen([str(chrome), url], close_fds=True)
    else:
        webbrowser.open(url)
    tracker.ok("L6-BROWSER-OPEN")


def main() -> int:
    tracker = LaunchTracker()
    os.chdir(ROOT)

    tracker.start("L0-ENV", "작업 디렉터리", str(ROOT))
    tracker.ok("L0-ENV", f"Python {sys.version.split()[0]}")

    tracker.start("L1-VENV", "venv 확인")
    python = _venv_python()
    if not python.is_file():
        return tracker.fail("L1-VENV", "venv 없음 - link_start.bat 으로 설치")
    tracker.ok("L1-VENV", str(python.name))

    tracker.start("L2-PORT-SCAN", "포트 LISTEN PID 스캔", f"{HOST}:{PORT}")
    pids = _port_pids()
    tracker.ok("L2-PORT-SCAN", f"pids={pids or 'none'}")

    tracker.start("L3-HEALTH", "GET /api/status + progress")
    ready, ready_detail = _existing_server_ready()
    if ready:
        tracker.ok("L3-HEALTH", ready_detail)
        _open_browser(tracker)
        tracker.start("L7-DONE", "완료", "기존 서버 사용")
        tracker.ok("L7-DONE")
        return 0

    kind, _, detail = _fetch_status()
    if kind == "empty":
        tracker.ok("L3-HEALTH", f"zombie - {detail}")
    elif kind == "network" and not pids:
        tracker.ok("L3-HEALTH", f"offline - {detail}")
    else:
        tracker.ok("L3-HEALTH", f"재기동 필요 - {ready_detail or detail}")

    if pids:
        tracker.start("L3b-KILL-ZOMBIE", "좀비 서버 종료", str(pids))
        for pid in pids:
            sub = f"L3b-KILL-{pid}"
            tracker.start(sub, f"taskkill pid={pid}")
            _kill_pid(pid)
            tracker.ok(sub)
        time.sleep(1.5)
        tracker.ok("L3b-KILL-ZOMBIE", "done")

        tracker.start("L3c-HEALTH-RETRY", "종료 후 재확인")
        kind2, _, detail2 = _fetch_status()
        if kind2 == "ok":
            tracker.ok("L3c-HEALTH-RETRY", "unexpected live")
        else:
            tracker.ok("L3c-HEALTH-RETRY", detail2)

    open_sock, sock_detail = _probe_socket()
    if open_sock and not pids:
        tracker.start("L3d-PORT-STUCK", "포트 점유 but PID 없음", sock_detail)
        tracker.ok("L3d-PORT-STUCK", "spawn 시도")

    tracker.start("L4-SPAWN", "서버 프로세스 생성")
    proc = _spawn_server(python, tracker)
    if proc is None:
        return tracker.fail("L4-SPAWN", "spawn 실패 - logs/link_ui.log 확인")
    tracker.ok("L4-SPAWN", f"pid={proc.pid}")

    tracker.start("L5-WAIT-HEALTH", "헬스 대기", f"최대 {HEALTH_WAIT_SEC}s")
    deadline = time.monotonic() + HEALTH_WAIT_SEC
    attempt = 0
    last_detail = ""
    while time.monotonic() < deadline:
        attempt += 1
        sub = f"L5-WAIT-{attempt:02d}"
        tracker.start(sub, f"헬스 폴링 #{attempt}")
        kind, _, last_detail = _fetch_status()
        if kind == "ok":
            tracker.ok(sub, last_detail)
            tracker.ok("L5-WAIT-HEALTH", f"ready after {attempt} tries")
            _open_browser(tracker)
            tracker.start("L7-DONE", "완료", BASE)
            tracker.ok("L7-DONE")
            return 0
        tracker.ok(sub, f"{kind}: {last_detail[:80]}")
        time.sleep(HEALTH_INTERVAL_SEC)

    if proc.poll() is not None:
        tracker.fail("L5-WAIT-HEALTH", f"서버 조기 종료 exit={proc.returncode}; {last_detail}")
    else:
        tracker.fail("L5-WAIT-HEALTH", f"타임아웃; 마지막={last_detail}; logs/link_ui.log 확인")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
