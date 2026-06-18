"""
Reject narrative or valuation tokens smuggled into mechanical fields.
기계적 필드에 끼어든 서술·평가 토큰 거부.

Purpose / 목적
--------------
Rule R08: scan crumbs and mechanism for banned sentiment/market narrative tokens.
Physical facts must remain mechanical for skeptic acceptance.
규칙 R08: 크럼·메커니즘에서 금지된 감정·시장 서술 토큰 스캔.
물리적 사실은 기계적이어야 수용 가능.

Pipeline position / 파이프라인 위치
---------------------------------
  registry NARRATIVE tier  →  NarrativeLeakRule

When to modify / 수정 시점
--------------------------
- Extend ``BANNED_NARRATIVE_TOKENS`` carefully — false positives reject valid crumbs.
- CJK tokens use raw substring scan because ``tokenize`` may not split them.

Key invariants / 핵심 불변조건
------------------------------
- FAIL → CORRELATION (not retry-eligible).
- Checks all text fields including proposed_mechanism.
"""

from __future__ import annotations

from deconstructor.skeptic.rules.base import tokenize
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)

# Tokens that indicate human narrative, not physical state.
BANNED_NARRATIVE_TOKENS = frozenset(
    {
        "bullish",
        "bearish",
        "good",
        "bad",
        "positive",
        "negative",
        "optimistic",
        "pessimistic",
        "crash",
        "boom",
        "surge",
        "plunge",
        "rally",
        "slump",
        "hot",
        "cold",
        "호재",
        "악재",
        "급등",
        "급락",
    }
)


def _collect_text(ctx: RuleContext) -> str:
    """
    Concatenate all hypothesis-relevant text for leak scanning.
    누출 스캔용 가설 관련 텍스트 전부 연결.

    Args:
        ctx: Rule context.

    Returns:
        Single space-joined string of subjects, changes, mechanism.

    수정 시 주의점:
        New crumb fields in pipeline require inclusion here.
    """
    parts = [
        ctx.source.subject,
        ctx.source.state_change,
        ctx.target.subject,
        ctx.target.state_change,
        ctx.hypothesis.proposed_mechanism,
    ]
    return " ".join(parts)


def find_narrative_leaks(text: str) -> set[str]:
    """
    Detect banned tokens in text via tokenize + raw substring for CJK.
    tokenize 및 CJK 원문 부분 문자열로 금지 토큰 탐지.

    Args:
        text: Combined crumb/mechanism text.

    Returns:
        Set of matched banned token strings.

    수정 시 주의점:
        Substring match may hit inside longer English words — curated list mitigates.
    """
    tokens = tokenize(text)
    # Also scan raw lowercased text for CJK tokens not split by tokenize.
    lowered = text.lower()
    leaks: set[str] = set()
    for banned in BANNED_NARRATIVE_TOKENS:
        if banned in tokens:
            leaks.add(banned)
        elif banned in lowered:
            leaks.add(banned)
    return leaks


class NarrativeLeakRule:
    """
    Rule 08 — Narrative or valuation tokens invalidate a hypothesis.
    규칙 08 — 서술·평가 토큰이 있으면 가설 무효.

    Physical facts must not contain market sentiment or moral judgment.

    수정 시 주의점:
        Runs early — narrative in source crumb fails entire pair regardless of target.
    """

    rule_id = "R08_NARRATIVE_LEAK"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Full rule context.

        Returns:
            FAIL with leak list if banned tokens found; PASS otherwise.

        수정 시 주의점:
            Sorted leak list in reason for stable test output.
        """
        leaks = find_narrative_leaks(_collect_text(ctx))
        if leaks:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.FAIL,
                classification=CausalClassification.CORRELATION,
                reason=f"narrative tokens detected: {sorted(leaks)}",
            )
        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.PASS,
            reason="no narrative tokens in crumbs or mechanism",
        )
