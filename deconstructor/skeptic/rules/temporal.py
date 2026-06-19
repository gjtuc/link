"""

Temporal ordering rules — cause must precede effect.

시간 순서 규칙 — 원인이 결과보다 앞서야 함.



Purpose / 목적

--------------

Rules R03–R04: enforce cause-before-effect and reject simultaneous correlation

without mechanism.

규칙 R03–R04: 원인-선행 강제, 메커니즘 없는 동시 상관 거부.



Pipeline position / 파이프라인 위치

---------------------------------

  registry TEMPORAL tier  →  TemporalOrderingRule, SimultaneousCooccurrenceRule



When to modify / 수정 시점

--------------------------

- Missing timestamps → ABSTAIN on both rules (not FAIL).

- R04 allows simultaneity PASS when proposed_mechanism non-empty.



Key invariants / 핵심 불변조건

------------------------------

- R03 FAIL: source timestamp after target → CORRELATION.

- R04 FAIL: equal timestamps without mechanism → CORRELATION.

"""



from __future__ import annotations



from deconstructor.skeptic.schemas import (

    CausalClassification,

    RuleCheckResult,

    RuleContext,

    RuleOutcome,

)





class TemporalOrderingRule:

    """

    Rule 03 — When timestamps exist, cause must occur before effect.

    규칙 03 — 타임스탬프가 있으면 원인이 결과보다 앞서야 함.



    Effect preceding cause indicates reverse causation or spurious correlation.



    수정 시 주의점:

        ``t_src <= t_tgt`` is PASS — equal time deferred to R04.

    """



    rule_id = "R03_TEMPORAL_ORDER"



    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:

        """

        Args:

            ctx: Source (cause) and target (effect) facts.



        Returns:

            ABSTAIN without timestamps; FAIL on reverse order; PASS on forward/equal.



        수정 시 주의점:

            Strict inequality fail only on ``t_src > t_tgt``.

        """

        t_src = ctx.source.timestamp

        t_tgt = ctx.target.timestamp



        if t_src is None or t_tgt is None:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.ABSTAIN,

                reason="timestamps missing - cannot verify temporal order",

            )



        if t_src > t_tgt:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.FAIL,

                classification=CausalClassification.CORRELATION,

                reason="source timestamp is after target - reverse temporal order",

            )



        return RuleCheckResult(

            rule_id=self.rule_id,

            outcome=RuleOutcome.PASS,

            reason="source precedes or equals target in time",

        )





class SimultaneousCooccurrenceRule:

    """

    Rule 04 — Exact simultaneous events without mechanism are correlation.

    규칙 04 — 메커니즘 없는 정확한 동시 사건은 상관.



    Co-occurrence at t=0 with no stated propagation path cannot be causal

    without additional mechanical evidence (handled by mechanism rules).



    수정 시 주의점:

        Only fires when timestamps equal exactly — not merely close in time.

    """



    rule_id = "R04_SIMULTANEOUS_COOCCURRENCE"



    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:

        """

        Args:

            ctx: Facts with timestamps and optional mechanism.



        Returns:

            ABSTAIN if time missing; PASS if not simultaneous or mechanism present;

            FAIL on simultaneous without mechanism.



        수정 시 주의점:

            Distinct from R11 zero-lag cross-domain — R04 is exact equality.

        """

        t_src = ctx.source.timestamp

        t_tgt = ctx.target.timestamp



        if t_src is None or t_tgt is None:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.ABSTAIN,

                reason="timestamps missing - cannot test simultaneity",

            )



        if t_src != t_tgt:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.PASS,

                reason="events are not simultaneous",

            )



        if ctx.hypothesis.proposed_mechanism.strip():

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.PASS,

                reason="simultaneous but explicit mechanism stated",

            )



        return RuleCheckResult(

            rule_id=self.rule_id,

            outcome=RuleOutcome.FAIL,

            classification=CausalClassification.CORRELATION,

            reason="simultaneous co-occurrence with no propagation mechanism",

        )


