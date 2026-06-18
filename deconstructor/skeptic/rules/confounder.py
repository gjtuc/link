"""
Post-hoc pattern — effect listed without preceding cause window.
사후(post-hoc) 패턴 — 선행 원인 구간 없이 결과만 나열.

Purpose / 목적
--------------
Rule R11: zero-lag cross-subject links without mechanism are suspicious correlation.
규칙 R11: 메커니즘 없이 주체가 다르고 지연이 0인 연결은 의심스러운 상관.

Pipeline position / 파이프라인 위치
---------------------------------
  registry TEMPORAL tier (after simultaneity)  →  PostHocLagRule

When to modify / 수정 시점
--------------------------
- ``_MIN_CAUSAL_LAG_MS = 1`` — sub-millisecond equality counts as zero lag.
- Same-subject zero lag ABSTAIN — may be valid fast state transition.

Key invariants / 핵심 불변조건
------------------------------
- Requires both timestamps; missing → ABSTAIN.
- Explicit mechanism bypasses zero-lag FAIL.
"""

from __future__ import annotations

from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)

# Minimum plausible propagation delay when both timestamps exist (ms).
_MIN_CAUSAL_LAG_MS = 1


class PostHocLagRule:
    """
    Rule 11 — Zero-lag distant domains without mechanism are suspicious.
    규칙 11 — 메커니즘 없는 제로 래그 원거리 도메인은 의심.

    When timestamps exist and lag is 0 but subjects differ, require mechanism.

    수정 시 주의점:
        FAIL is CORRELATION — distinct from R04 simultaneity wording but similar cases.
    """

    rule_id = "R11_POST_HOC_ZERO_LAG"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Facts with optional timestamps and proposed_mechanism.

        Returns:
            PASS on positive lag, mechanism, or ABSTAIN paths; FAIL on zero-lag cross-subject.

        수정 시 주의점:
            Negative lag should have failed R03 — lag_ms still computed for edge cases.
        """
        t_src = ctx.source.timestamp
        t_tgt = ctx.target.timestamp

        if t_src is None or t_tgt is None:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="timestamps missing",
            )

        if ctx.source.subject.lower() == ctx.target.subject.lower():
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="same subject - zero lag may be valid",
            )

        lag_ms = int((t_tgt - t_src).total_seconds() * 1000)

        if lag_ms >= _MIN_CAUSAL_LAG_MS:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason=f"positive lag {lag_ms}ms between domains",
            )

        if ctx.hypothesis.proposed_mechanism.strip():
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason="zero lag but explicit mechanism",
            )

        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.CORRELATION,
            reason="zero lag across different subjects without mechanism",
        )
