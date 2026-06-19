"""비동기 전체 분석 — POST 즉시 반환, 백그라운드 실행, 결과 폴링."""

from __future__ import annotations

import threading
import traceback
from typing import Any, Callable

_lock = threading.Lock()
_running = False
_result: dict[str, Any] | None = None
_error: dict[str, Any] | None = None


def is_analyze_running() -> bool:
    with _lock:
        return _running


def get_analyze_result() -> dict[str, Any] | None:
    with _lock:
        return dict(_result) if _result else None


def get_analyze_error() -> dict[str, Any] | None:
    with _lock:
        return dict(_error) if _error else None


def start_analyze_job(worker: Callable[[], dict[str, Any]]) -> bool:
    """백그라운드에서 worker 실행. 이미 실행 중이면 False."""
    global _running, _result, _error
    with _lock:
        if _running:
            return False
        _running = True
        _result = None
        _error = None

    def _run() -> None:
        global _running, _result, _error
        try:
            payload = worker()
            with _lock:
                if payload.get("ok"):
                    _result = payload
                    _error = None
                else:
                    _error = payload
                    _result = None
        except Exception as exc:
            with _lock:
                _error = {
                    "ok": False,
                    "error": str(exc),
                    "detail": traceback.format_exc(limit=8),
                    "failed_step": "S9-ASYNC",
                }
                _result = None
        finally:
            with _lock:
                _running = False

    threading.Thread(target=_run, daemon=True, name="deconstructor-analyze").start()
    return True
