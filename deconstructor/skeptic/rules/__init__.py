"""

Codified skeptic rules — one module per rule family.

코딩된 스케ptic 규칙 — 규칙 패밀리별 모듈.



Purpose / 목적

--------------

Public re-exports for rule classes and registry symbols used by engine/tests.

엔진·테스트가 사용하는 규칙 클래스·레지스트리 심볼 공개 재export.



Pipeline position / 파이프라인 위치

---------------------------------

  rules/registry.DEFAULT_RULES  →  SkepticEngine



When to modify / 수정 시점

--------------------------

- New rule module: add to registry.py and optionally export here.



Key invariants / 핵심 불변조건

------------------------------

- Evaluation order defined only in registry.build_rule_registry.

"""



from deconstructor.skeptic.rules.registry import (

    DEFAULT_RULES,

    RULE_BY_ID,

    RegisteredRule,

    build_rule_registry,

)

from deconstructor.skeptic.rules.common_cause import CommonCausePatternRule

from deconstructor.skeptic.rules.identity import (

    DuplicateFactPairRule,

    NoSelfLoopRule,

)

from deconstructor.skeptic.rules.mechanism import (

    MechanismPlausibilityRule,

    ProposedMechanismRule,

)



__all__ = [

    "DEFAULT_RULES",

    "RULE_BY_ID",

    "RegisteredRule",

    "build_rule_registry",

    "CommonCausePatternRule",

    "DuplicateFactPairRule",

    "MechanismPlausibilityRule",

    "NoSelfLoopRule",

    "ProposedMechanismRule",

]


