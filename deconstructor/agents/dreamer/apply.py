"""
Step 2 — DreamHypothesis → AtomicFact 변환 (Micro-step S2-5)
=============================================================

Purpose / 목적
--------------
Pro(또는 stub)가 반환한 ``DreamHypothesisList`` 를 파이프라인 ``AtomicFact`` 로 변환.

Provenance (고정)
-----------------
  source_type=inferred
  check_status=pending  → 그래프 노랑, Fact-Checker 입력 대기

Dreamer anchor
--------------
  ``anchor_fact_id`` = hypothesis.source_fact_id (ripples from 한 파랑 fact).
  시각화: hover 시 숨김 점선(visualizer) · Neo4j MERGE(weaver).

Micro-steps
-----------
  S2-5-a  source index 구축
  S2-5-b  각 hypothesis 검증·변환 (unknown source_fact_id → SKIP)
  S2-5-c  완료 로그
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from deconstructor.agents.dreamer.schemas import DreamHypothesis, DreamHypothesisList
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-5] {msg}"
    logger.info(line)
    print(line)


def _resolve_timestamp(
    hypothesis: DreamHypothesis,
    source_index: dict[str, AtomicFact],
) -> datetime | None:
    source = source_index.get(hypothesis.source_fact_id)
    if source is None or source.timestamp is None:
        return None
    if hypothesis.lag_minutes is None:
        return source.timestamp
    return source.timestamp + timedelta(minutes=hypothesis.lag_minutes)


def apply_hypotheses(
    result: DreamHypothesisList,
    source_facts: list[AtomicFact],
) -> list[AtomicFact]:
    """
    DreamHypothesisList → AtomicFact 리스트 (inferred/pending).

    Micro-steps:
      S2-5-a  source index 구축
      S2-5-b  각 hypothesis 검증·변환
      S2-5-c  완료 로그
    """
    source_index = {f.id: f for f in source_facts}
    _log(f"apply start: {len(result.hypotheses)} hypotheses, {len(source_index)} sources")

    inferred: list[AtomicFact] = []
    for i, hyp in enumerate(result.hypotheses, 1):
        if hyp.source_fact_id not in source_index:
            _log(f"SKIP hyp[{i}] unknown source_fact_id={hyp.source_fact_id[:8]}..")
            continue

        ts = _resolve_timestamp(hyp, source_index)
        fact = AtomicFact(
            subject=hyp.subject,
            state_change=hyp.state_change,
            timestamp=ts,
            is_atomic=True,
            reasoning=hyp.mechanism,
            source_type="inferred",
            check_status="pending",
            anchor_fact_id=hyp.source_fact_id,
        )
        _log(
            f"hyp[{i}] -> AtomicFact id={fact.id[:8]}.. "
            f"subject={fact.subject!r} inferred/pending"
        )
        inferred.append(fact)

    _log(f"apply complete: {len(inferred)} inferred fact(s)")
    return inferred
