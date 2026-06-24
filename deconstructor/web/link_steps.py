"""
Link UI 분석 단계 추적 — 단계 코드·오류 위치 기록
==================================================

각 단계는 ``step`` 코드(예: ``S4-1-NODE-deconstruct``)로 로그·API 응답에 남긴다.
실패 시 ``failed_step`` + ``steps`` 배열로 UI에서 어디서 멈췄는지 표시.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from deconstructor.print_util import safe_print


@dataclass
class LinkStepRecord:
    step: str
    label: str
    status: str  # running | ok | error | skip
    detail: str = ""
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LinkStepTracker:
    """분석 배치 단계별 상태 — 배치 1회당 1개 인스턴스."""

    def __init__(self, on_change: Callable[["LinkStepTracker"], None] | None = None) -> None:
        self.steps: list[LinkStepRecord] = []
        self.failed_step: str | None = None
        self._current: str | None = None
        self._on_change = on_change

    def _notify(self) -> None:
        if self._on_change:
            self._on_change(self)

    def start(self, step: str, label: str, detail: str = "") -> None:
        self._current = step
        self.steps.append(LinkStepRecord(step=step, label=label, status="running", detail=detail))
        line = f"[LinkUI:{step}] {label}"
        if detail:
            line += f" — {detail}"
        safe_print(line)
        self._notify()

    def ok(self, step: str | None = None, detail: str = "") -> None:
        code = step or self._current
        if not code:
            return
        for rec in reversed(self.steps):
            if rec.step == code and rec.status == "running":
                rec.status = "ok"
                if detail:
                    rec.detail = detail
                safe_print(f"[LinkUI:{code}] OK {detail}".rstrip())
                self._notify()
                return
        self._notify()

    def skip(self, step: str, label: str, detail: str = "") -> None:
        self.steps.append(
            LinkStepRecord(step=step, label=label, status="skip", detail=detail)
        )
        safe_print(f"[LinkUI:{step}] SKIP {label} {detail}".rstrip())
        self._notify()

    def fail(self, exc: BaseException, *, step: str | None = None) -> dict[str, Any]:
        code = step or self._current or "S9-UNKNOWN"
        if self.failed_step is None:
            self.failed_step = code
        msg = str(exc)
        tb = traceback.format_exc(limit=8)
        for rec in reversed(self.steps):
            if rec.step == code and rec.status == "running":
                rec.status = "error"
                rec.detail = msg[:500]
                break
        else:
            self.steps.append(
                LinkStepRecord(step=code, label="오류", status="error", detail=msg[:500])
            )
        safe_print(f"[LinkUI:{code}] ERROR {msg}")
        safe_print(tb)
        self._notify()
        return {
            "ok": False,
            "failed_step": self.failed_step,
            "error": msg,
            "detail": tb,
            "steps": self.to_list(),
        }

    def to_list(self) -> list[dict[str, str]]:
        return [
            {
                "step": r.step,
                "label": r.label,
                "status": r.status,
                "detail": r.detail,
                "at": r.at,
            }
            for r in self.steps
        ]
