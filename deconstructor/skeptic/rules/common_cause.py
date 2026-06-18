"""
Common-cause pattern detection.
공통 원인(common-cause) 패턴 탐지.

Purpose / 목적
--------------
Rule R05: detect parallel effects on unrelated subjects with similar state_change
at the same (or missing) time — likely spurious direct A→B edge.
규칙 R05: 무관한 주체에 유사 state_change가 동시(또는 시간 없음)에 나타나는
평행 효과 — 직접 A→B 가설은 허위일 가능성.

Pipeline position / 파이프라인 위치
---------------------------------
  registry STRUCTURAL tier  →  CommonCausePatternRule

When to modify / 수정 시점
--------------------------
- Jaccard threshold 0.5 on state_change tokens — tune with fixtures catalog.
- Stated mechanism overrides FAIL → PASS (retry path can salvage).

Key invariants / 핵심 불변조건
------------------------------
- Same subject ABSTAIN — not a common-cause parallel pattern.
- FAIL classification is CORRELATION (not retry-eligible).
"""

from __future__ import annotations

from deconstructor.skeptic.rules.base import tokenize
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleContext,
    RuleOutcome,
)


class CommonCausePatternRule:
    """
    Rule 05 — Parallel effects with unrelated subjects are likely common-caused.
    규칙 05 — 무관 주체의 평행 효과는 공통 원인 가능성.

    Pattern: different subjects, highly similar state_change verbs, same or
    missing timestamps → direct A→B edge is probably spurious correlation.

    수정 시 주의점:
        PASS default when pattern not matched — does not prove causation alone.
    """

    rule_id = "R05_COMMON_CAUSE_PATTERN"

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Args:
            ctx: Source/target facts and optional mechanism.

        Returns:
            FAIL CORRELATION on parallel pattern; PASS or ABSTAIN otherwise.

        수정 시 주의점:
            ``both_timeless`` treats missing timestamps like simultaneous correlation risk.
        """
        src_subj = ctx.source.subject.lower().strip()
        tgt_subj = ctx.target.subject.lower().strip()

        if src_subj == tgt_subj:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="same subject — not a common-cause parallel pattern",
            )

        src_tokens = tokenize(ctx.source.state_change)
        tgt_tokens = tokenize(ctx.target.state_change)
        if not src_tokens or not tgt_tokens:
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.ABSTAIN,
                reason="insufficient state_change tokens",
            )

        overlap = src_tokens & tgt_tokens
        jaccard = len(overlap) / len(src_tokens | tgt_tokens)

        same_time = (
            ctx.source.timestamp is not None
            and ctx.target.timestamp is not None
            and ctx.source.timestamp == ctx.target.timestamp
        )
        both_timeless = (
            ctx.source.timestamp is None and ctx.target.timestamp is None
        )

        if jaccard >= 0.5 and (same_time or both_timeless):
            if ctx.hypothesis.proposed_mechanism.strip():
                # Direct mechanism assertion overrides parallel-pattern heuristic.
                return RuleCheckResult(
                    rule_id=self.rule_id,
                    outcome=RuleOutcome.PASS,
                    reason="parallel pattern but direct mechanism overrides",
                )
            return RuleCheckResult(
                rule_id=self.rule_id,
                outcome=RuleOutcome.FAIL,
                classification=CausalClassification.CORRELATION,
                reason=(
                    "parallel effects on unrelated subjects with similar "
                    "state_change — likely common cause, not direct link"
                ),
            )

        return RuleCheckResult(
            rule_id=self.rule_id,
            outcome=RuleOutcome.PASS,
            reason="no common-cause parallel pattern detected",
        )
