"""

Central ordered registry of all skeptic rules.

모든 스케ptic 규칙의 중앙 순서 레지스트리.



Purpose / 목적

--------------

Single source of truth for rule evaluation order, tier metadata, and

``DEFAULT_RULES`` list consumed by ``SkepticEngine``.

규칙 평가 순서·티어 메타데이터·``SkepticEngine``이 쓰는 ``DEFAULT_RULES``의 단일 출처.



Pipeline position / 파이프라인 위치

---------------------------------

  **build_rule_registry**  →  DEFAULT_RULES  →  SkepticEngine.run_rules



When to modify / 수정 시점

--------------------------

- Insert new rules in tier order: IDENTITY → NARRATIVE → TEMPORAL → STRUCTURAL → MECHANISM.

- Reordering changes "first FAIL" aggregator behavior — update truth_table if needed.

- 새 규칙은 티어 순서에 삽입; 순서 변경 시 집계기 첫 FAIL 의미가 바뀜.



Key invariants / 핵심 불변조건

------------------------------

- ``RULE_BY_ID`` rebuilt on import — duplicate rule_id strings last-wins silently.

- Registry lists 11 rules (R01–R11); batch Rule 12 lives in batch_filter.py.

- 11개 per-pair 규칙; 배치 규칙 12는 batch_filter.

"""



from __future__ import annotations



from dataclasses import dataclass



from deconstructor.skeptic.rules.base import SkepticRule

from deconstructor.skeptic.rules.chain import EntityStateChainRule

from deconstructor.skeptic.rules.common_cause import CommonCausePatternRule

from deconstructor.skeptic.rules.confounder import PostHocLagRule

from deconstructor.skeptic.rules.identity import DuplicateFactPairRule, NoSelfLoopRule

from deconstructor.skeptic.rules.isolation import CrossDomainIsolationRule

from deconstructor.skeptic.rules.mechanism import (

    MechanismPlausibilityRule,

    ProposedMechanismRule,

)

from deconstructor.skeptic.rules.narrative import NarrativeLeakRule

from deconstructor.skeptic.rules.temporal import (

    SimultaneousCooccurrenceRule,

    TemporalOrderingRule,

)

from deconstructor.skeptic.rules.tiers import RuleTier





@dataclass(frozen=True)

class RegisteredRule:

    """

    Metadata for one codified rule.

    코딩된 규칙 하나의 메타데이터.



    ``tier`` is documentary for humans/tools — engine uses list order only.

    """



    rule: SkepticRule

    tier: RuleTier

    description: str





def build_rule_registry() -> list[RegisteredRule]:

    """

    Return all rules in strict evaluation order.

    엄격한 평가 순서로 모든 규칙 반환.



    Returns:

        Ordered ``RegisteredRule`` entries from identity through mechanism tiers.



    수정 시 주의점:

        Early identity/temporal fails short-circuit aggregator but all rules still run

        in engine — order affects trace only, not skip logic.

    """

    return [

        RegisteredRule(

            NoSelfLoopRule(), RuleTier.IDENTITY, "reject self-loops"

        ),

        RegisteredRule(

            DuplicateFactPairRule(), RuleTier.IDENTITY, "reject duplicate pairs"

        ),

        RegisteredRule(

            NarrativeLeakRule(), RuleTier.NARRATIVE, "reject narrative tokens"

        ),

        RegisteredRule(

            TemporalOrderingRule(), RuleTier.TEMPORAL, "cause before effect"

        ),

        RegisteredRule(

            SimultaneousCooccurrenceRule(),

            RuleTier.TEMPORAL,

            "reject simultaneous correlation",

        ),

        RegisteredRule(

            PostHocLagRule(), RuleTier.TEMPORAL, "reject zero-lag cross-domain"

        ),

        RegisteredRule(

            CommonCausePatternRule(),

            RuleTier.STRUCTURAL,

            "reject parallel common-cause pattern",

        ),

        RegisteredRule(

            CrossDomainIsolationRule(),

            RuleTier.STRUCTURAL,

            "reject zero-overlap domains",

        ),

        RegisteredRule(

            EntityStateChainRule(),

            RuleTier.STRUCTURAL,

            "pass ordered same-entity chains",

        ),

        RegisteredRule(

            MechanismPlausibilityRule(),

            RuleTier.MECHANISM,

            "require propagation path",

        ),

        RegisteredRule(

            ProposedMechanismRule(),

            RuleTier.MECHANISM,

            "validate stated mechanism",

        ),

    ]





DEFAULT_RULES: list[SkepticRule] = [

    entry.rule for entry in build_rule_registry()

]



RULE_BY_ID: dict[str, RegisteredRule] = {

    entry.rule.rule_id: entry for entry in build_rule_registry()

}


