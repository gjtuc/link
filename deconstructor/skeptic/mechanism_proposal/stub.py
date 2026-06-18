"""
Stub mechanism text for dry-run.
드라이런용 스텁 메커니즘 텍스트.

Purpose / 목적
--------------
Deterministic mechanism strings for CI and ``dry_run=True`` retry path without LLM.
CI 및 ``dry_run=True`` 재시도에서 LLM 없이 결정론적 메커니즘 문자열 제공.

Pipeline position / 파이프라인 위치
---------------------------------
  fill.proposals_for_inconclusive_stub  →  **stub_mechanism**

When to modify / 수정 시점
--------------------------
- Stub must include both subjects and state changes so R07 can PASS on retry.
- Changing format affects fixture expectations for retry tests.
- R07 통과를 위해 양쪽 subject·state_change 포함 필수.

Key invariants / 핵심 불변조건
------------------------------
- Always non-empty string (satisfies ``MechanismProposal.min_length=1``).
"""

from __future__ import annotations

from deconstructor.models import AtomicFact


def stub_mechanism(source: AtomicFact, target: AtomicFact) -> str:
    """
    Build template mechanism sentence from two facts.
    두 사실로부터 템플릿 메커니즘 문장 생성.

    Args:
        source: Cause crumb.
        target: Effect crumb.

    Returns:
        Single sentence linking source and target subject/state_change.

    수정 시 주의점:
        Token overlap with crumbs is intentional for R07 ``touches_source/target``.
    """
    return (
        f"{source.subject} {source.state_change} propagates to "
        f"{target.subject} {target.state_change}"
    )
