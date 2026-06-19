"""
Human hypothesis — MVP 서비스 오케스트레이션
============================================

단계 (LinkStepTracker ``H*`` 코드)
---------------------------------
  H1-VALIDATE   anchor Neo4j 조회·provenance
  H2-BUILD      AtomicFact 생성
  H3-NEO4J      단건 MERGE
  H4-RENDER     graph_output.html 갱신

v1 이후 Fact-Checker·Skeptic 단계는 여기에 이어 붙인다.
"""

from __future__ import annotations

from deconstructor.web.graph_refresh import refresh_graph_from_neo4j
from deconstructor.web.human_hypothesis.factory import build_human_inferred_fact
from deconstructor.web.human_hypothesis.schemas import (
    HumanHypothesisCreate,
    HumanHypothesisResult,
)
from deconstructor.web.human_hypothesis.store import (
    HumanHypothesisStoreError,
    load_anchor_fact,
    merge_human_hypothesis_fact,
)
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.viz.neo4j_utils import neo4j_is_available


def submit_human_hypothesis(payload: HumanHypothesisCreate) -> dict:
    """
    사용자 가설 1건 제출 (MVP).

    Returns:
        ``HumanHypothesisResult`` dict (+ 실패 시 ``ok=False``·``steps``).
    """
    tracker = LinkStepTracker()
    try:
        return _submit_inner(payload, tracker)
    except HumanHypothesisStoreError as exc:
        return tracker.fail(exc, step="H1-VALIDATE")
    except Exception as exc:
        return tracker.fail(exc, step="H0-UNKNOWN")


def _submit_inner(payload: HumanHypothesisCreate, tracker: LinkStepTracker) -> dict:
    tracker.start("H0-NEO4J-PING", "Neo4j 연결 확인")
    if not neo4j_is_available():
        raise RuntimeError(
            "Neo4j에 연결할 수 없습니다. Link UI에서 분석을 한 번 실행하거나 "
            "Neo4j Desktop을 켜 주세요."
        )
    tracker.ok("H0-NEO4J-PING")

    tracker.start("H1-VALIDATE", "원천 노드 검증", payload.anchor_fact_id[:12])
    anchor = load_anchor_fact(payload.anchor_fact_id)
    tracker.ok("H1-VALIDATE", anchor.subject[:40])

    tracker.start("H2-BUILD", "AtomicFact 생성", payload.subject[:40])
    fact = build_human_inferred_fact(payload, anchor_timestamp=anchor.timestamp)
    tracker.ok("H2-BUILD", f"id={fact.id[:8]}..")

    tracker.start("H3-NEO4J", "가설 MERGE")
    merge_human_hypothesis_fact(fact)
    tracker.ok("H3-NEO4J")

    tracker.start("H4-RENDER", "그래프 HTML 갱신")
    refreshed = refresh_graph_from_neo4j()
    tracker.ok("H4-RENDER", "ok" if refreshed else "skip")

    result = HumanHypothesisResult(
        fact_id=fact.id,
        anchor_fact_id=fact.anchor_fact_id or payload.anchor_fact_id,
        subject=fact.subject,
        state_change=fact.state_change,
        graph_refreshed=refreshed,
        steps=tracker.to_list(),
        message="사용자 가설이 저장되었습니다 (노란 pending 노드).",
    )
    return result.model_dump()
