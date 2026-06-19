"""

Identity and duplication rules.

동일성·중복 규칙.



Purpose / 목적

--------------

Rules R01–R02: reject logically invalid or information-free hypothesis pairs

before temporal/structural checks.

규칙 R01–R02: 시간·구조 검사 전 논리적으로 무효하거나 정보 없는 가설 쌍 거부.



Pipeline position / 파이프라인 위치

---------------------------------

  registry IDENTITY tier (first)  →  NoSelfLoopRule, DuplicateFactPairRule



When to modify / 수정 시점

--------------------------

- R01 also guarded at hypothesis generation — rule remains defense in depth.

- Case-insensitive subject/state_change comparison for R02.



Key invariants / 핵심 불변조건

------------------------------

- Both rules FAIL with CORRELATION classification for aggregator A1.

"""



from __future__ import annotations



from deconstructor.skeptic.schemas import (

    CausalClassification,

    RuleCheckResult,

    RuleContext,

    RuleOutcome,

)

from deconstructor.skeptic.rules.base import SkepticRule





class NoSelfLoopRule:

    """

    Rule 01 — A fact cannot cause itself.

    규칙 01 — 사실이 자기 자신의 원인이 될 수 없음.



    Self-loops are logical impossibilities for directed causal edges.



    수정 시 주의점:

        Compares fact ids, not subject text — distinct ids with same content hit R02.

    """



    rule_id = "R01_NO_SELF_LOOP"



    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:

        """

        Args:

            ctx: Source and target AtomicFact with ids.



        Returns:

            FAIL if ids equal; PASS otherwise.



        수정 시 주의점:

            Should be unreachable from generate_pairwise_hypotheses — keep for custom hypotheses.

        """

        if ctx.source.id == ctx.target.id:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.FAIL,

                classification=CausalClassification.CORRELATION,

                reason="source and target are the same fact id",

            )

        return RuleCheckResult(

            rule_id=self.rule_id,

            outcome=RuleOutcome.PASS,

            reason="distinct fact ids",

        )





class DuplicateFactPairRule:

    """

    Rule 02 — Reject pairs that describe the same subject + state_change.

    규칙 02 — 동일 subject + state_change 쌍 거부.



    Duplicate crumbs provide no new causal information — linking them is

    pure correlation of identical observations.



    수정 시 주의점:

        Whitespace stripped; case folded for comparison.

    """



    rule_id = "R02_DUPLICATE_PAIR"



    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:

        """

        Args:

            ctx: Source and target crumbs.



        Returns:

            FAIL when both subject and state_change match; PASS otherwise.



        수정 시 주의점:

            Same subject different change may pass — entity chain rules apply later.

        """

        same_subject = (

            ctx.source.subject.lower().strip()

            == ctx.target.subject.lower().strip()

        )

        same_change = (

            ctx.source.state_change.lower().strip()

            == ctx.target.state_change.lower().strip()

        )



        if same_subject and same_change:

            return RuleCheckResult(

                rule_id=self.rule_id,

                outcome=RuleOutcome.FAIL,

                classification=CausalClassification.CORRELATION,

                reason="identical subject and state_change - duplicate observation",

            )



        return RuleCheckResult(

            rule_id=self.rule_id,

            outcome=RuleOutcome.PASS,

            reason="facts are not duplicates",

        )


