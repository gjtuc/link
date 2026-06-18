"""
Mechanical propagation plausibility rules.
기계적 전파 타당성 규칙.

Purpose / 목적
--------------
Rules R06 and R07: require token-level propagation path or valid stated mechanism
before accepting bare co-mention as causal.
규칙 R06·R07: 맨 공기재(co-mention)를 인과로 받기 전 토큰 수준 전파 경로 또는
유효한 제안 메커니즘 요구.

Pipeline position / 파이프라인 위치
---------------------------------
  registry MECHANISM tier  →  MechanismPlausibilityRule  →  ProposedMechanismRule

When to modify / 수정 시점
--------------------------
- R06 PASS on non-empty ``proposed_mechanism`` bypasses token path check — retry depends on this.
- R07 FAIL uses INCONCLUSIVE (not CORRELATION) — enables mechanism fill retry.

Key invariants / 핵심 불변조건
------------------------------
- R06 runs before R07; empty mechanism still evaluated by R06 token overlap.
"""

from __future__ import annotations

from deconstructor.skeptic.rules.propagation import has_propagation_path
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)
from deconstructor.skeptic.rules.base import tokenize


class MechanismPlausibilityRule:
    """
    Rule 06 — Bare co-mention without propagation path is correlation.
    규칙 06 — 전파 경로 없는 공기재는 상관.

    Requires token-level mechanical overlap between cause and effect crumbs.

    수정 시 주의점:
        Explicit mechanism short-circuits to PASS — must be non-whitespace strip.
    """

    rule_id = "R06_MECHANISM_PLAUSIBILITY"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Includes optional hypothesis.proposed_mechanism from retry.

        Returns:
            PASS if mechanism stated or propagation path exists; else FAIL CORRELATION.

        수정 시 주의점:
            Changing to INCONCLUSIVE FAIL would alter retry eligibility — keep CORRELATION.
        """
        if ctx.hypothesis.proposed_mechanism.strip():
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason="explicit proposed_mechanism present",
            )

        if has_propagation_path(ctx):
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason="token-level propagation path between crumbs",
            )

        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.CORRELATION,
            reason="no mechanical propagation path - correlation only",
        )


class ProposedMechanismRule:
    """
    Rule 07 — If mechanism is stated, it must reference both subjects or changes.
    규칙 07 — 메커니즘이 있으면 양쪽 subject 또는 change를 참조해야 함.

    Prevents vacuous mechanism strings that smuggle narrative without linkage.

    수정 시 주의점:
        ABSTAIN when no mechanism — R06 already judged bare crumbs.
    """

    rule_id = "R07_PROPOSED_MECHANISM"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Hypothesis may carry LLM/stub proposed_mechanism.

        Returns:
            ABSTAIN if no mechanism; PASS if tokens touch both crumbs; else INCONCLUSIVE FAIL.

        수정 시 주의점:
            INCONCLUSIVE FAIL triggers retry — vacuous LLM output should land here.
        """
        mechanism = ctx.hypothesis.proposed_mechanism.strip()
        if not mechanism:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="no proposed mechanism to validate",
            )

        mech_tokens = tokenize(mechanism)
        src_tokens = tokenize(ctx.source.subject) | tokenize(ctx.source.state_change)
        tgt_tokens = tokenize(ctx.target.subject) | tokenize(ctx.target.state_change)

        touches_source = bool(mech_tokens & src_tokens)
        touches_target = bool(mech_tokens & tgt_tokens)

        if touches_source and touches_target:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason="mechanism references both crumbs",
            )

        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.INCONCLUSIVE,
            reason="mechanism does not reference both source and target crumbs",
        )
