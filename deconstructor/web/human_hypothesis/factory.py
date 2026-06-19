"""
Human hypothesis — AtomicFact 변환 (MVP)
========================================

Dreamer ``apply_hypotheses`` 와 **동일한 provenance** 를 쓰되,
Dreamer LLM 호출 없이 사용자 입력만으로 fact 를 만든다.

  source_type = inferred
  check_status = pending   → 그래프 노란 노드
  author = human           → 툴팁·Neo4j 감사 추적 (v3)
  anchor_fact_id = 원천 파란 노드 id
"""

from __future__ import annotations

from datetime import datetime, timezone

from deconstructor.models import AtomicFact
from deconstructor.web.human_hypothesis.schemas import HumanHypothesisCreate


def build_human_inferred_fact(
    payload: HumanHypothesisCreate,
    *,
    anchor_timestamp: datetime | None = None,
) -> AtomicFact:
    """
    사용자 가설 입력 → pending inferred AtomicFact.

    Args:
        payload: API/모달에서 검증된 3(+1)필드.
        anchor_timestamp: 원천 fact 시각. 있으면 가설 시각을 +1분으로
            잡아 TemporalOrderingRule 이 읽을 수 있게 한다 (선택).

    Returns:
        is_atomic=True — verify 루프 없이 바로 그래프·DB 대상.
    """
    ts: datetime | None = None
    if anchor_timestamp is not None:
        from datetime import timedelta

        ts = anchor_timestamp + timedelta(minutes=1)

    return AtomicFact(
        subject=payload.subject,
        state_change=payload.state_change,
        timestamp=ts or datetime.now(timezone.utc),
        is_atomic=True,
        reasoning=payload.mechanism,
        source_type="inferred",
        check_status="pending",
        anchor_fact_id=payload.anchor_fact_id,
        author="human",
    )
