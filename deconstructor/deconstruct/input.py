"""
input — deconstruct 노드 입력 해석 (Target Resolution)
======================================================

## 목적 / Purpose

현재 `State`에서 **이번 패스에 분해할 텍스트·부모 ID·refining 여부**를 결정한다.
LLM 경로와 스텁 경로의 입력 규칙이 다르므로 resolver를 분리했다.

Determines **text, parent ID, and refining flag** for the current deconstruct pass
from `State`. LLM and stub paths use different resolvers.

## 파이프라인 위치 / Pipeline Position

::

    State → resolve_*_target → DeconstructTarget → node → LLM/stub

`recursion_depth == 0` 이고 `extracted_facts` 비어 있음 → 초기 헤드라인 분해.
`extracted_facts` 비어 있지 않음 → 첫 pending crumb 재분해 (refining=True).

When `recursion_depth == 0` and `extracted_facts` is empty → initial headline split.
When `extracted_facts` is non-empty → re-split first pending crumb (`refining=True`).

## 수정 가이드 / Modification Guide

- **LLM vs stub 분리 유지**: 프롬프트는 subject|state_change, 스텁은 raw_text 고정.
- pending 선택 정책 변경(예: FIFO → 우선순위) 시 두 resolver 모두 검토.
- `DeconstructTarget` 필드 추가 시 `node.py` / `stub_node.py` / 테스트 동시 수정.
- `None` 반환 = 분해 종료 신호; 라우팅은 verify/routing이 담당.
"""

from __future__ import annotations

from dataclasses import dataclass

from deconstructor.pipeline.state import State


@dataclass(frozen=True)
class DeconstructTarget:
    """
    What the deconstruct node should split on this pass.

    이번 deconstruct 패스에서 분해할 대상 스냅샷 (불변).
    """

    text: str
    parent_id: str | None
    refining: bool
    use_raw_headline: bool


def resolve_stub_target(state: State) -> DeconstructTarget | None:
    """
    Dry-run stub always refines using the original headline text.

    스텁: 항상 raw_text 사용. refining 시 parent_id=pending[0].id.
    """
    pending = state["extracted_facts"]

    # 초기 진입: 헤드라인 전체, 부모 없음
    if not pending and state["recursion_depth"] == 0:
        return DeconstructTarget(
            text=state["raw_text"],
            parent_id=None,
            refining=False,
            use_raw_headline=True,
        )

    # 루프 재진입: 동일 raw_text로 스텁 시나리오의 2단계 분해
    if pending:
        return DeconstructTarget(
            text=state["raw_text"],
            parent_id=pending[0].id,
            refining=True,
            use_raw_headline=True,
        )

    return None


def resolve_llm_target(state: State) -> DeconstructTarget | None:
    """
    LLM path uses subject|state_change when refining a non-atomic crumb.

    LLM: 재분해 시 `subject | state_change` 문자열로 프롬프트에 전달.
    """
    pending = state["extracted_facts"]

    if not pending and state["recursion_depth"] == 0:
        return DeconstructTarget(
            text=state["raw_text"],
            parent_id=None,
            refining=False,
            use_raw_headline=False,
        )

    if pending:
        target = pending[0]
        # 비원자 crumb 하나를 더 잘게 쪼개기 위한 축약 표현
        return DeconstructTarget(
            text=f"{target.subject} | {target.state_change}",
            parent_id=target.id,
            refining=True,
            use_raw_headline=False,
        )

    return None
