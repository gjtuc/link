"""
Entity-internal state chains — same subject, ordered time.
동일 주체 내부 상태 사슬 — 같은 subject, 시간 순서.

Purpose / 목적
--------------
Rule R10: positive structural signal when one entity undergoes ordered state changes.
Prevents false isolation rejects for legitimate intra-system chains.
규칙 R10: 한 엔티티의 순서 있는 상태 변화에 대한 긍정 구조 신호.
정당한 시스템 내 사슬이 격리 규칙에 걸리지 않게 함.

Pipeline position / 파이프라인 위치
---------------------------------
  registry (STRUCTURAL tier)  →  EntityStateChainRule  — after isolation, before mechanism

When to modify / 수정 시점
--------------------------
- PASS does not alone prove causation — aggregator still needs no FAIL from other rules.
- Reverse-time same-entity ABSTAINs (R03 handles temporal fail).

Key invariants / 핵심 불변조건
------------------------------
- Requires shared subject tokens, distinct state_change, source time <= target time.
"""

from __future__ import annotations

from deconstructor.skeptic.rules.propagation import shared_subject
from deconstructor.skeptic.schemas import (
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)


class EntityStateChainRule:
    """
    Rule 10 — Same entity, ordered timestamps, distinct state changes.
    규칙 10 — 동일 엔티티, 순서 있는 타임스탬프, 서로 다른 state_change.

    This is a positive structural signal for causation within one system.
    Does not alone prove causality but prevents false isolation rejects.

    수정 시 주의점:
        ABSTAIN-heavy — only PASS when strict chain pattern matches.
    """

    rule_id = "R10_ENTITY_STATE_CHAIN"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Hypothesis context with source/target facts.

        Returns:
            PASS for ordered same-entity chains; ABSTAIN otherwise.

        수정 시 주의점:
            Identical state_change ABSTAIN — duplicate pairs should fail at R02 first.
        """
        if not shared_subject(ctx):
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="different subjects - not an entity chain",
            )

        if ctx.source.state_change.strip().lower() == ctx.target.state_change.strip().lower():
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="identical state_change - not a chain",
            )

        t_src = ctx.source.timestamp
        t_tgt = ctx.target.timestamp
        if t_src is None or t_tgt is None:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="timestamps missing for chain check",
            )

        if t_src <= t_tgt:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.PASS,
                reason="ordered states on same entity",
            )

        # Effect before cause on same entity — temporal tier (R03) is authoritative.
        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.ABSTAIN,
            reason="reverse time on same entity - R03 handles",
        )
