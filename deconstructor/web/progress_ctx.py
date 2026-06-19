"""파이프라인 노드 내부 — LinkStepTracker 하위 단계 (contextvar)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deconstructor.web.link_steps import LinkStepTracker

_tracker: ContextVar[LinkStepTracker | None] = ContextVar("dc_progress_tracker", default=None)
_node_step: ContextVar[str] = ContextVar("dc_progress_node_step", default="")


def bind_progress(tracker: LinkStepTracker, *, node_step: str = "") -> None:
    _tracker.set(tracker)
    _node_step.set(node_step)


def set_node_step(node_step: str) -> None:
    _node_step.set(node_step)


def unbind_progress() -> None:
    _tracker.set(None)
    _node_step.set("")


@contextmanager
def progress_sub(suffix: str, label: str, detail: str = ""):
    """노드 안의 실제 작업(LLM 호출·루프 1건 등)마다 하위 단계 기록."""
    tr = _tracker.get()
    base = _node_step.get()
    if tr is None or not base:
        yield
        return
    step = f"{base}-{suffix}"
    tr.start(step, label, detail)
    try:
        yield
    except Exception as exc:
        tr.fail(exc, step=step)
        raise
    else:
        tr.ok(step, detail[:160] if detail else "")


def progress_detail(detail: str) -> None:
    """실행 중인 마지막 running 단계의 detail만 갱신 (새 단계 없음)."""
    tr = _tracker.get()
    if tr is None:
        return
    for rec in reversed(tr.steps):
        if rec.status == "running":
            rec.detail = detail[:500]
            tr._notify()
            return
