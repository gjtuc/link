"""
Human-in-the-loop 가설 — 웹 UI 증분 입력 (MVP)
==============================================

사용자가 완성된 인과 그래프의 **파란(extracted) 노드**에서 이어
자신의 가설을 적으면 Dreamer 출력과 동일한 ``AtomicFact`` 형태로
Neo4j에 저장한다.

단계별 로드맵 (구현 순서)
-------------------------
  MVP (이 패키지 1차) — 저장 + 노란 노드 표시만
  v1 — Fact-Checker 단건 실행
  v2 — Skeptic + CAUSES + 그래프 갱신
  v3 — 자유 텍스트 파싱, session_id 필터

모듈 구성
---------
  schemas   — API 요청/응답 Pydantic
  factory   — HumanHypothesisCreate → AtomicFact
  store     — Neo4j anchor 검증·단건 MERGE
  service   — MVP 오케스트레이션 (H* 단계)
"""

from deconstructor.web.human_hypothesis.schemas import (
    HumanHypothesisCreate,
    HumanHypothesisResult,
)
from deconstructor.web.human_hypothesis.service import submit_human_hypothesis

__all__ = [
    "HumanHypothesisCreate",
    "HumanHypothesisResult",
    "submit_human_hypothesis",
]
