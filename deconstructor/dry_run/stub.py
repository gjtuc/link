"""Deterministic FactList payloads for dry-run deconstruction passes.
드라이런 분해 패스용 결정론적 FactList 페이로드.

Purpose / 목적
--------------
Replaces LLM deconstruct output with three scripted passes:
- **initial**: one compound non-atomic crumb (forces loop-back).
- **refine**: two ordered atomic crumbs (grid → factory) for skeptic edges.
- **stuck**: compound crumb that never reaches null floor (depth-cap tests).
LLM deconstruct 대체 스크립트 3종:
- **initial**: 비원자 1개 → 루프백.
- **refine**: 시간순 원자 2개(grid→factory) → 스켉틱 엣지.
- **stuck**: null floor 불가 복합 조각 → 깊이 상한 테스트.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    graph deconstruct node (dry_run=True)
        --> stub_decompose(headline, refining=...)
        --> FactList --> State.extracted_facts

``refining`` flag comes from graph (pass 0 vs pass 1+).
``refining``은 그래프가 패스 0/1+ 구분해 전달.

Temporal design / 시간 설계
---------------------------
``_T0`` and +30s offset let skeptic rules R03/R06 accept grid→factory causality.
``_T0``·+30초로 grid→factory 인과 스켉틱 규칙(R03/R06) 통과.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Do not call LLM APIs here.
- ``is_depth_cap_headline`` branch uses ``stub_decompose_pass_stuck`` on refine.
- Changing timestamps affects skeptic golden tests — coordinate with ``skeptic/`` rules.
- LLM 호출 금지; 타임스탬프 변경 시 skeptic 골든 테스트 동기화.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from deconstructor.dry_run.modes import is_depth_cap_headline, strip_dryrun_prefix
from deconstructor.dry_run.subject import parse_subject
from deconstructor.models import AtomicFact, FactList

# Fixed anchor time for reproducible skeptic latency/temporal rules.
# 스켉틱 시간 규칙 재현용 고정 기준 시각.
_T0 = datetime(2026, 6, 18, 9, 0, 0)


def stub_decompose_pass_initial(headline: str) -> FactList:
    """
    Pass 0: one compound non-atomic crumb.

    Forces ``verify`` to keep it in ``extracted_facts`` and route back to
    ``deconstruct``.

    패스 0: 비원자 복합 조각 1개 → verify가 extracted에 유지·deconstruct 재라우팅.
    """
    subject = parse_subject(headline)
    return FactList(
        facts=[
            AtomicFact(
                subject=subject,
                state_change="power_supply -> lost",
                is_atomic=False,
                reasoning="compound event - split into grid and input paths",
            ),
        ]
    )


def stub_decompose_pass_refine(headline: str) -> FactList:
    """
    Pass 1+: two atomic crumbs with temporal ordering for skeptic.

    ``grid`` precedes ``factory`` by 30s so R03/R06 can accept one edge.

    패스 1+: 스켉틱용 시간순 원자 2개 (grid가 factory보다 30초 앞).
    """
    subject = parse_subject(headline)
    return FactList(
        facts=[
            AtomicFact(
                subject="grid",
                state_change="power -> off",
                timestamp=_T0,
                is_atomic=True,
                reasoning="single grid power loss",
            ),
            AtomicFact(
                subject=subject,
                state_change="power_input -> lost",
                timestamp=_T0 + timedelta(seconds=30),
                is_atomic=True,
                reasoning="single factory input loss",
            ),
        ]
    )


def stub_decompose_pass_stuck(headline: str) -> FactList:
    """
    Refine pass that never reaches the null floor.

    Each refine replaces one compound crumb with another compound crumb so
    the loop would run forever without ``max_recursion_depth``.

    정제마다 복합→복합 교체로 null floor 불가; 상한 없으면 무한 루프.
    """
    subject = parse_subject(headline)
    return FactList(
        facts=[
            AtomicFact(
                subject=subject,
                state_change="subsystem_state -> unresolved",
                is_atomic=False,
                reasoning="still compound after refine - depth cap will truncate",
            ),
        ]
    )


def stub_decompose(headline: str, *, refining: bool) -> FactList:
    """Dispatch to initial, refine, or depth-cap-stuck stub pass.
    initial / refine / depth-cap-stuck 스텁 패스로 분기."""
    if is_depth_cap_headline(headline):
        bare = strip_dryrun_prefix(headline)
        if refining:
            return stub_decompose_pass_stuck(bare)
        return stub_decompose_pass_initial(bare)

    if refining:
        return stub_decompose_pass_refine(headline)
    return stub_decompose_pass_initial(headline)
