"""JSON serialization for pipeline State.
파이프라인 State JSON 직렬화.

Purpose / 목적
--------------
``state_to_json`` dumps the LangGraph ``State`` TypedDict (including nested
Pydantic models) to a pretty-printed UTF-8 JSON string for debugging,
regression snapshots, and machine-readable archives.
LangGraph ``State`` TypedDict(중첩 Pydantic 모델 포함)를 디버깅·회귀 스냅샷·
기계 가독 archive용 들여쓰기 JSON 문자열로 덤프합니다.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    graph.invoke() / TracedRun.final_state  --->  state_to_json()  --->  .json file

Parallel to human report formatters; does not affect graph execution.
사람용 리포트 포맷터와 병렬; 그래프 실행에 영향 없음.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Extend ``_default`` only for new non-JSON-serializable types in State; prefer
  Pydantic ``model_dump(mode="json")`` on domain models.
- Keep ``ensure_ascii=False`` so Korean headlines and fact subjects render correctly.
- Do not add business logic or state mutation here.
- State 필드에 비-JSON 타입 추가 시 ``_default`` 확장; 도메인 모델은
  ``model_dump(mode="json")`` 우선.
- ``ensure_ascii=False`` 유지 (한글 헤드라인·주어 보존).
- 비즈니스 로직·state 변경 금지.
"""

from __future__ import annotations

import json

from deconstructor.pipeline.state import State


def state_to_json(state: State) -> str:
    """Serialize State to indented JSON string.
    State를 들여쓰기 JSON 문자열로 직렬화."""

    def _default(obj: object) -> object:
        # Pydantic v2 models (AtomicFact, CausalEdge, WeaverResult, etc.)
        # Pydantic v2 모델은 model_dump로 dict 변환.
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        raise TypeError(type(obj))

    return json.dumps(state, default=_default, ensure_ascii=False, indent=2)
