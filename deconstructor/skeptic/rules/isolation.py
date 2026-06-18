"""
Cross-domain isolation — zero mechanical overlap.
교차 도메인 격리 — 기계적 토큰 겹침 없음.

Purpose / 목적
--------------
Rule R09: unrelated subjects with zero shared tokens → direct causal edge spurious.
Stricter pre-check before R06 mechanism plausibility.
규칙 R09: 무관 주체·공유 토큰 0 → 직접 인과 엣지 허위. R06 이전 선행 검사.

Pipeline position / 파이프라인 위치
---------------------------------
  registry STRUCTURAL  →  CrossDomainIsolationRule  (before R10 chain, before R06)

When to modify / 수정 시점
--------------------------
- Stated mechanism → ABSTAIN (defer to R07) — isolation does not FAIL when mechanism present.
- Uses ``is_cross_domain_isolated`` from propagation.py.

Key invariants / 핵심 불변조건
------------------------------
- Shared subject → not isolated (helper returns False).
- FAIL classification CORRELATION.
"""

from __future__ import annotations

from deconstructor.skeptic.rules.propagation import is_cross_domain_isolated
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)


class CrossDomainIsolationRule:
    """
    Rule 09 — Unrelated domains with zero token overlap are correlation.
    규칙 09 — 무관 도메인·토큰 겹침 0은 상관.

    Stricter pre-check before mechanism plausibility: if crumbs share no
    vocabulary at all, a direct causal edge is spurious.

    수정 시 주의점:
        ABSTAIN with mechanism — R06/R07 must still validate propagation text.
    """

    rule_id = "R09_CROSS_DOMAIN_ISOLATION"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Source/target crumbs and optional mechanism.

        Returns:
            ABSTAIN if mechanism stated; FAIL if isolated; PASS if tokens overlap.

        수정 시 주의점:
            PASS only means non-zero overlap — R06 still required for acceptance.
        """
        if ctx.hypothesis.proposed_mechanism.strip():
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="mechanism stated - isolation deferred to R07",
            )

        if is_cross_domain_isolated(ctx):
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.FAIL,
                classification=CausalClassification.CORRELATION,
                reason="zero token overlap across unrelated subjects",
            )

        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.PASS,
            reason="domains share at least one mechanical token",
        )
