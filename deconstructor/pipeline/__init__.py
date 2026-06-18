"""Pipeline package — shared state, partial-run detection, execution trace.
파이프라인 패키지 — 공유 state, 부분 실행 감지, 실행 추적.

Purpose / 목적
--------------
Public surface for **orchestration helpers** that sit beside the LangGraph
definition in ``deconstructor.graph``: typed ``State``, initial state factory,
partial-run classification, and traced execution (``pipeline.trace``).
LangGraph 정의(``deconstructor.graph``) 옆의 **오케스트레이션 헬퍼**:
``State``, 초기 state 팩토리, partial-run 판별, 추적 실행.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    make_initial_state()  -->  graph.stream / invoke  -->  State
                                    |
                                    v
                            detect_partial_run (nodes)
                                    |
                                    v
                            run_pipeline_traced (optional observability)

This package does **not** define graph nodes — only state shape and runners.
그래프 **노드 정의 없음** — state 형태와 runner만.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- New State keys: update ``state.py``, ``state_factory.py``, graph nodes, and
  report/trace handlers together.
- Export only stable helpers from ``__all__``; trace API lives in ``pipeline.trace``.
- State 키 추가 시 state·factory·graph·report·trace 핸들러 동시 수정.
"""

from deconstructor.pipeline.partial_run import PartialRunInfo, detect_partial_run

__all__ = ["PartialRunInfo", "detect_partial_run"]
