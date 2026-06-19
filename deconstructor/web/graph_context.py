"""
그래프 표시 컨텍스트 — 마지막 분석 배치 필터
============================================

Neo4j ``stock`` DB 는 **모든 실행 결과를 누적**한다.
그래프 HTML 은 기본적으로 **마지막 ``전체 분석 시작`` 배치**의
``analysis_run_id``(배치 UUID) 만 보여 주도록 필터한다.

``trigger_event``(원문) 는 UI·디버그용으로 함께 보관한다.
"""

from __future__ import annotations

from threading import Lock

_lock = Lock()
_last_analysis_run_id: str | None = None
_last_trigger_events: list[str] | None = None


def normalize_trigger_event(text: str) -> str:
    """저장·조회 시 공백 정규화 (줄바꿈·연속 공백)."""
    return " ".join(text.split()).strip()


def set_last_graph_filter(
    *,
    analysis_run_id: str,
    trigger_events: list[str] | None = None,
) -> None:
    """배치 분석 직후 호출 — 그래프·갱신 API 가 동일 필터를 쓴다."""
    global _last_analysis_run_id, _last_trigger_events
    with _lock:
        _last_analysis_run_id = analysis_run_id.strip() or None
        if not trigger_events:
            _last_trigger_events = None
        else:
            seen: set[str] = set()
            unique: list[str] = []
            for te in trigger_events:
                norm = normalize_trigger_event(te)
                if norm and norm not in seen:
                    seen.add(norm)
                    unique.append(norm)
            _last_trigger_events = unique or None


def set_last_trigger_events(events: list[str] | None) -> None:
    """레거시 호출 — ``analysis_run_id`` 없이 trigger 만 갱신 (비권장)."""
    global _last_trigger_events
    with _lock:
        if not events:
            _last_trigger_events = None
        else:
            seen: set[str] = set()
            unique: list[str] = []
            for te in events:
                norm = normalize_trigger_event(te)
                if norm and norm not in seen:
                    seen.add(norm)
                    unique.append(norm)
            _last_trigger_events = unique or None


def get_last_analysis_run_id() -> str | None:
    with _lock:
        return _last_analysis_run_id


def get_last_trigger_events() -> list[str] | None:
    with _lock:
        return list(_last_trigger_events) if _last_trigger_events else None


def get_graph_filter_snapshot() -> dict:
    """브라우저 ``?debug=1``·``/api/graph-filter`` 용 스냅샷."""
    with _lock:
        events = list(_last_trigger_events) if _last_trigger_events else []
        return {
            "analysis_run_id": _last_analysis_run_id,
            "trigger_events": events,
            "trigger_preview": events[0][:80] if events else None,
        }
