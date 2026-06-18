"""
state_merge — deconstruction State 병합 헬퍼 (격리 테스트용)
============================================================

## 목적 / Purpose

LangGraph 노드 밖에서 테스트 가능한 **순수 상태 병합** 유틸리티를 제공한다.
비원자 부모 crumb 하나를 더 세분화된 자식 facts 목록으로 교체한다.

Provides **pure state-merge** utilities testable outside LangGraph nodes.
Replaces one non-atomic parent crumb with a list of finer child facts.

## 파이프라인 위치 / Pipeline Position

::

    deconstruct/apply.apply_deconstruct_result → merge_refined_facts

재분해(refining) 패스에서만 호출된다. 초기 분해(`parent_id is None`)는 이 함수를 거치지 않음.

Called only on refine passes (`parent_id` set). Initial decomposition
(`parent_id is None`) bypasses this function.

## 수정 가이드 / Modification Guide

- ID 충돌·중복 자식 처리 정책 변경 시 `apply.py`와 deconstruct 노드 동시 검토.
- 자식 순서 보존이 중요하면 `without_parent + children` 순서 유지.
- 다중 부모 동시 교체가 필요하면 새 함수 추가; 기존 시그니처는 단일 parent_id 전제.
- 단위 테스트: `tests/`에서 pending 리스트 fixture로 직접 호출 권장.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact


def merge_refined_facts(
    existing: list[AtomicFact],
    parent_id: str,
    children: list[AtomicFact],
) -> list[AtomicFact]:
    """
    Replace one non-atomic parent crumb with finer children.

    parent_id에 해당하는 fact를 제거하고 children을 끝에 이어 붙인 새 리스트 반환.
    """
    # 부모 crumb 제외한 나머지 pending 유지
    without_parent = [f for f in existing if f.id != parent_id]
    # 자식 facts append — 순서: 기존 pending(부모 제외) + 새 children
    return without_parent + children
