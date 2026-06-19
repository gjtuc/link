"""전체 분석 진행률 — LinkStepTracker 완료 단계만 반영 (시간 보간 없음)."""

from __future__ import annotations

import re
import threading
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from deconstructor.web.link_steps import LinkStepRecord, LinkStepTracker

_lock = threading.Lock()
_active_tracker: LinkStepTracker | None = None
_state: dict[str, Any] = {
    "running": False,
    "job_id": "",
    "percent": 0,
    "label": "",
    "ok_steps": 0,
    "source_count": 1,
    "phase": "",
    "planned_budget": 0.0,
}

# step 코드 → 가중치 (완료 시에만 earned에 합산)
_STEP_WEIGHTS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"^S0-"), 1.0),
    (re.compile(r"^S2-"), 1.2),
    (re.compile(r"^S1-"), 1.0),
    (re.compile(r"^S3-"), 1.0),
    (re.compile(r"COMPILE"), 1.0),
    (re.compile(r"-INIT$"), 0.8),
    (re.compile(r"-PREP$"), 0.8),
    (re.compile(r"-LLM$"), 4.0),
    (re.compile(r"-FLASH$"), 5.0),
    (re.compile(r"-PRO$"), 5.0),
    (re.compile(r"-FC-\d+"), 3.0),
    (re.compile(r"-SKEPTIC-"), 3.5),
    (re.compile(r"NODE-deconstruct"), 1.5),
    (re.compile(r"NODE-verify"), 1.0),
    (re.compile(r"NODE-dreamer"), 1.0),
    (re.compile(r"NODE-fact_checker"), 1.0),
    (re.compile(r"NODE-skeptic"), 1.5),
    (re.compile(r"NODE-weaver"), 2.0),
    (re.compile(r"-REPORT$"), 0.8),
    (re.compile(r"-SESSION-GRAPH"), 1.0),
    (re.compile(r"^S5-"), 1.5),
    (re.compile(r"^S6-"), 1.2),
    (re.compile(r"^S7-"), 1.0),
    (re.compile(r"-DONE$"), 0.5),
]


def _weight_for_step(step: str) -> float:
    for pat, weight in _STEP_WEIGHTS:
        if pat.search(step):
            return weight
    return 1.0


def _budget_for_sources(source_count: int) -> float:
    """1건·dreamer 경로 기준 보수적 예상 가중치 합."""
    per_source = (
        0.8  # PREP
        + 1.0  # COMPILE
        + 0.8  # INIT
        + 1.5
        + 4.0  # deconstruct node shell + LLM
        + 1.0  # verify
        + 1.0
        + 5.0
        + 5.0  # dreamer flash + pro
        + 1.0
        + 3.0 * 3  # fact_checker ~3 hypotheses
        + 1.5
        + 3.5  # skeptic
        + 2.0  # weaver
        + 0.5  # DONE
    )
    global_tail = 1.0 + 1.0 + 3.0 + 1.2 + 1.0 + 3.0 + 0.5
    return global_tail + per_source * max(1, source_count)


def _earned_weight(steps: list[LinkStepRecord]) -> float:
    return sum(
        _weight_for_step(rec.step)
        for rec in steps
        if rec.status in ("ok", "skip")
    )


def _started_weight(steps: list[LinkStepRecord]) -> float:
    return sum(_weight_for_step(rec.step) for rec in steps)


def compute_percent_from_steps(
    steps: list[LinkStepRecord],
    *,
    source_count: int = 1,
    planned_budget: float | None = None,
) -> tuple[int, str, str]:
    """완료된 단계 가중치 / 예상 총 가중치 → (percent, label, phase_code)."""
    earned = _earned_weight(steps)
    started = _started_weight(steps)
    budget = planned_budget or _budget_for_sources(source_count)
    # 이미 시작된 단계·남은 파이프라인 여유 반영
    budget = max(budget, started + 6.0, earned + 4.0)

    pct = int(100 * earned / max(budget, 1.0))
    pct = max(0, min(97, pct))

    running_rec = None
    for rec in reversed(steps):
        if rec.status == "running":
            running_rec = rec
            break

    if running_rec:
        detail = f" — {running_rec.detail}" if running_rec.detail else ""
        label = f"{running_rec.label}{detail}"
        phase = running_rec.step
    elif steps and earned >= budget * 0.85:
        label = "그래프 저장·렌더 중…"
        phase = "S7-RENDER"
    elif steps:
        label = "다음 단계 준비…"
        phase = steps[-1].step
    else:
        label = "시작 중…"
        phase = "S0-START"
    return pct, label[:160], phase


def bind_tracker(tracker: LinkStepTracker | None) -> None:
    global _active_tracker
    _active_tracker = tracker


def _refresh_from_tracker_locked() -> None:
    tr = _active_tracker
    if not tr or not _state.get("running"):
        return
    src_n = int(_state.get("source_count") or 1)
    planned = float(_state.get("planned_budget") or 0.0)
    earned = _earned_weight(tr.steps)
    started = _started_weight(tr.steps)
    planned = max(planned, _budget_for_sources(src_n), started + 6.0)
    _state["planned_budget"] = planned

    pct, label, phase = compute_percent_from_steps(
        tr.steps,
        source_count=src_n,
        planned_budget=planned,
    )
    prev = int(_state.get("percent") or 0)
    _state["percent"] = max(prev, pct)
    _state["label"] = label
    _state["phase"] = phase
    _state["ok_steps"] = sum(1 for r in tr.steps if r.status == "ok")


def set_source_count(count: int) -> None:
    with _lock:
        if _state.get("running"):
            _state["source_count"] = max(1, count)


def set_label(label: str, *, percent: int | None = None) -> None:
    with _lock:
        if not _state.get("running"):
            return
        _state["label"] = label[:160]
        if percent is not None:
            prev = int(_state.get("percent") or 0)
            _state["percent"] = max(prev, int(percent))


def begin_job(*, source_count: int = 1) -> str:
    job_id = str(uuid.uuid4())
    src = max(1, source_count)
    with _lock:
        bind_tracker(None)
        _state.update(
            {
                "running": True,
                "job_id": job_id,
                "percent": 0,
                "label": "시작 중…",
                "ok_steps": 0,
                "source_count": src,
                "phase": "S0-START",
                "planned_budget": _budget_for_sources(src),
            }
        )
    return job_id


def sync_tracker(tracker: LinkStepTracker) -> None:
    global _active_tracker
    with _lock:
        _active_tracker = tracker
        if not _state.get("running"):
            return
        _refresh_from_tracker_locked()


def finish_job() -> None:
    with _lock:
        bind_tracker(None)
        _state.update(
            {
                "running": False,
                "percent": 100,
                "label": "완료",
                "phase": "DONE",
            }
        )


def clear_job() -> None:
    with _lock:
        bind_tracker(None)
        _state.update(
            {
                "running": False,
                "job_id": "",
                "percent": 0,
                "label": "",
                "ok_steps": 0,
                "phase": "",
                "planned_budget": 0.0,
            }
        )


def snapshot() -> dict[str, Any]:
    with _lock:
        _refresh_from_tracker_locked()
        return dict(_state)
