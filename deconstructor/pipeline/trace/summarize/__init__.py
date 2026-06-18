"""Trace summarization package — StepRecord from node updates.
추적 요약 패키지 — 노드 update에서 StepRecord 생성.

Purpose / 목적
--------------
Exports ``summarize_update`` which turns a LangGraph partial state ``update``
dict into one ``StepRecord`` via the handler registry in ``summarize/handlers``.
LangGraph partial ``update`` dict를 ``summarize/handlers`` 레지스트리로
``StepRecord`` 하나로 변환하는 ``summarize_update`` 노출.

Pipeline position / 파이프라인 위치
-----------------------------------
Called once per node per stream event inside ``trace/runner.py``.
``trace/runner.py``의 stream 이벤트마다 노드당 1회 호출.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Add field-specific logic in ``handlers/<field>.py``, not here.
- ``compose.summarize_update`` orchestrates only — keep it thin.
- 필드별 로직은 handlers; compose는 얇게 유지.
"""

from deconstructor.pipeline.trace.summarize.compose import summarize_update

__all__ = ["summarize_update"]
