"""
Token overlap helpers for mechanism and isolation rules.
메커니즘·격리 규칙용 토큰 겹침 헬퍼.

Purpose / 목적
--------------
Shared mechanical token logic for R05–R10, R06, R09 — propagation carriers,
Jaccard, cross-domain isolation predicates.
R05–R10, R06, R09가 공유하는 기계적 토큰 로직 — 전파 매개체, Jaccard, 교차 도메인 격리.

Pipeline position / 파이프라인 위치
---------------------------------
  Imported by rules/* — not invoked directly by engine.

When to modify / 수정 시점
--------------------------
- ``PROPAGATION_CARRIERS`` expansion affects R06 PASS rate — update fixtures.
- ``has_propagation_path`` is inclusive (subject ref, shared subject, carriers, any shared token).

Key invariants / 핵심 불변조건
------------------------------
- All helpers read-only from ``RuleContext`` — no side effects.
- ``is_cross_domain_isolated``: different subjects AND zero shared tokens.
"""

from __future__ import annotations

from deconstructor.skeptic.rules.base import tokenize
from deconstructor.skeptic.schemas import RuleContext

# Mechanical nouns suggesting physical coupling between domains.
PROPAGATION_CARRIERS = frozenset(
    {
        "power",
        "supply",
        "signal",
        "pressure",
        "flow",
        "current",
        "voltage",
        "heat",
        "fuel",
        "water",
        "steam",
        "data",
        "network",
        "grid",
        "line",
        "pipe",
        "cable",
        "motor",
        "pump",
        "valve",
        "switch",
        "relay",
    }
)


def all_tokens(fact_subject: str, fact_change: str) -> set[str]:
    """
    Union of tokens from subject and state_change fields.
    subject와 state_change 필드 토큰 합집합.

    Args:
        fact_subject: Entity/subject string.
        fact_change: State change string.

    Returns:
        Token set for one crumb.

    수정 시 주의점:
        Uses same tokenize rules as narrative/mechanism rules.
    """
    return tokenize(fact_subject) | tokenize(fact_change)


def shared_tokens(ctx: RuleContext) -> set[str]:
    """
    Intersection of all tokens between source and target crumbs.
    원인·결과 크럼 전체 토큰 교집합.

    Args:
        ctx: Rule context.

    Returns:
        Tokens appearing in both source and target (any field).

    수정 시 주의점:
        Empty set triggers R09 isolation when subjects also differ.
    """
    src = all_tokens(ctx.source.subject, ctx.source.state_change)
    tgt = all_tokens(ctx.target.subject, ctx.target.state_change)
    return src & tgt


def jaccard_state_change(ctx: RuleContext) -> float:
    """
    Jaccard similarity on state_change tokens only (used by R05).
    state_change 토큰만 Jaccard 유사도 (R05용).

    Args:
        ctx: Rule context.

    Returns:
        0.0 if either side has no tokens; else |∩|/|∪|.

    수정 시 주의점:
        Duplicates R05 inline jaccard — keep formulas aligned if changing.
    """
    src = tokenize(ctx.source.state_change)
    tgt = tokenize(ctx.target.state_change)
    if not src or not tgt:
        return 0.0
    return len(src & tgt) / len(src | tgt)


def subject_references_effect(ctx: RuleContext) -> bool:
    """
    True if source subject tokens appear in target state_change.
    원인 subject 토큰이 결과 state_change에 있으면 True.

    Args:
        ctx: Rule context.

    Returns:
        Whether source entity is named in effect state description.

    수정 시 주의점:
        One-directional check — not symmetric.
    """
    return bool(tokenize(ctx.source.subject) & tokenize(ctx.target.state_change))


def shared_subject(ctx: RuleContext) -> bool:
    """
    True if source and target subject fields share tokens.
    원인·결과 subject 필드가 토큰을 공유하면 True.

    Args:
        ctx: Rule context.

    Returns:
        Entity overlap signal for R10 chain rule.

    수정 시 주의점:
        Token overlap, not raw string equality — "pump" vs "main pump" may match.
    """
    return bool(tokenize(ctx.source.subject) & tokenize(ctx.target.subject))


def has_carrier_overlap(ctx: RuleContext) -> bool:
    """
    True if shared tokens include a propagation carrier noun.
    공유 토큰에 전파 매개체 명사가 있으면 True.

    Args:
        ctx: Rule context.

    Returns:
        Carrier-mediated coupling hint.

    수정 시 주의점:
        Subset of ``has_propagation_path`` — not used alone in rules.
    """
    return bool(shared_tokens(ctx) & PROPAGATION_CARRIERS)


def has_propagation_path(ctx: RuleContext) -> bool:
    """
    Inclusive predicate for R06 — any mechanical linkage signal.
    R06용 포괄 판정 — 기계적 연결 신호가 하나라도 있으면 True.

    Args:
        ctx: Rule context.

    Returns:
        True if subject references effect, shared subject, carrier overlap, or any shared token.

    수정 시 주의점:
        Very permissive — R09 may still FAIL zero-overlap cross-domain pairs first.
    """
    if subject_references_effect(ctx):
        return True
    if shared_subject(ctx):
        return True
    shared = shared_tokens(ctx)
    if shared & PROPAGATION_CARRIERS:
        return True
    return bool(shared)


def is_cross_domain_isolated(ctx: RuleContext) -> bool:
    """
    True when crumbs share zero tokens and have different subjects.
    주체가 다르고 공유 토큰이 0이면 True.

    Args:
        ctx: Rule context.

    Returns:
        Isolation predicate for R09 FAIL.

    수정 시 주의점:
        Shared subject → False even if state_change tokens disjoint.
    """
    if shared_subject(ctx):
        return False
    return len(shared_tokens(ctx)) == 0
