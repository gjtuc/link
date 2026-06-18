"""Dry-run package — deterministic stubs without live LLM deconstruction.
드라이런 패키지 — 실 LLM 분해 없이 결정론적 스텁.

Purpose / 목적
--------------
Provides **headline parsing**, **scenario matrix**, **mode prefixes**, and
``stub_decompose`` FactList payloads so the full LangGraph pipeline (verify,
skeptic, weaver) can run offline with predictable facts and edges.
**헤드라인 파싱**, **시나리오 매트릭스**, **모드 접두사**, ``stub_decompose``
FactList로 verify·skeptic·weaver 전체 그래프를 예측 가능한 오프라인 실행.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    headline --> parse_subject / is_depth_cap_headline
        --> stub_decompose (graph deconstruct node when dry_run=True)
        --> State --> report

Replaces LLM deconstruct node only; does not stub verify/skeptic/weaver logic.
LLM deconstruct 노드만 대체; verify/skeptic/weaver는 실제 로직.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- New scenario: add ``HeadlineScenario`` in ``scenarios.py`` + stub branch if needed.
- Keep ``DEPTH_CAP_PREFIX`` stable — tests and matrix rely on exact string.
- Stubs must respect ``is_atomic`` flags — they drive graph routing.
- 시나리오는 ``scenarios.py``; ``DEPTH_CAP_PREFIX`` 문자열 변경 시 테스트 갱신.
- ``is_atomic``이 그래프 라우팅을 결정 — 스텁에서 정확히 설정.
"""

from deconstructor.dry_run.stub import stub_decompose
from deconstructor.dry_run.subject import SUFFIXES, parse_subject
from deconstructor.dry_run.scenarios import (
    DEPTH_CAP_SCENARIO,
    HEADLINE_SCENARIOS,
    HeadlineScenario,
)
from deconstructor.dry_run.modes import DEPTH_CAP_PREFIX, is_depth_cap_headline

__all__ = [
    "DEPTH_CAP_PREFIX",
    "DEPTH_CAP_SCENARIO",
    "HEADLINE_SCENARIOS",
    "HeadlineScenario",
    "SUFFIXES",
    "is_depth_cap_headline",
    "parse_subject",
    "stub_decompose",
]
