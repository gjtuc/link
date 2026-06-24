"""Factory for initial LangGraph State before graph.invoke/stream.
graph.invoke/stream 전 초기 LangGraph State 팩토리.

Purpose / 목적
--------------
``make_initial_state`` builds a zeroed ``State`` dict from ``raw_text`` and
resolves ``max_recursion_depth`` from explicit arg, ``config``, or module default.
``raw_text``와 깊이 상한(인자 > config > 모듈 기본)으로 초기 ``State`` dict 생성.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    CLI / run_pipeline_traced / tests
        --> make_initial_state(raw_text)
        --> graph entry

First code that touches State; no LLM or DB calls.
State를 처음 만드는 코드; LLM·DB 호출 없음.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Resolution order for depth cap: ``max_recursion_depth`` arg >
  ``config.MAX_DECOMPOSITION_ITERATIONS`` > ``MAX_RECURSION_DEPTH`` (5).
- Every new ``State`` key needs a default here matching ``state.py``.
- Dry-run scenarios may pass lower caps via ``HeadlineScenario.max_recursion_depth``.
- 깊이: 인자 > config > 5.
- ``State`` 신규 키는 여기 기본값 필수.
"""

from __future__ import annotations

import uuid

from deconstructor import config
from deconstructor.pipeline.state import State

# Fallback when config and caller omit explicit cap.
# config·호출자 모두 생략 시 폴백.
MAX_RECURSION_DEPTH = 5


def make_initial_state(
    raw_text: str,
    *,
    max_recursion_depth: int | None = None,
    enable_dreamer: bool = False,
    analysis_run_id: str | None = None,
    source_document_meta: dict[str, str | int] | None = None,
    corpus_fact_pool: list | None = None,
) -> State:
    """Create fresh State dict ready for graph.stream / invoke."""
    cap = (
        max_recursion_depth
        or config.MAX_DECOMPOSITION_ITERATIONS
        or MAX_RECURSION_DEPTH
    )
    return {
        "raw_text": raw_text,
        "analysis_run_id": analysis_run_id or str(uuid.uuid4()),
        "source_document_meta": dict(source_document_meta or {}),
        "extracted_facts": [],
        "completed_facts": [],
        "recursion_depth": 0,
        "max_recursion_depth": cap,
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "inferred_facts": [],
        "dreamer_log": [],
        "promoted_facts": [],
        "dropped_hypotheses": [],
        "fact_checker_log": [],
        "enable_dreamer": enable_dreamer,
        "verified_edges_pass1": [],
        "pass2_gap_nodes": [],
        "skeptic_pass1_log": [],
        "corpus_fact_pool": list(corpus_fact_pool or []),
        "weaver_result": None,
    }
