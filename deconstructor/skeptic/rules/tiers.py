"""

Rule tier ordering for The Skeptic pipeline.

The Skeptic 파이프라인 규칙 티어 순서.



Purpose / 목적

--------------

Document logical grouping of rules (identity, narrative, temporal, structural, mechanism).

Not enforced at runtime beyond registry list order.

규칙 논리 그룹(identity, narrative, temporal, structural, mechanism) 문서화.

런타임은 registry 리스트 순서만 따름.



Pipeline position / 파이프라인 위치

---------------------------------

  registry.RegisteredRule.tier  — metadata only



When to modify / 수정 시점

--------------------------

- Add new tier values only if registry gains a new family — keep enum stable for tooling.



Key invariants / 핵심 불변조건

------------------------------

- Lower tiers conceptually run first because registry respects this ordering.

"""



from __future__ import annotations



from enum import Enum





class RuleTier(str, Enum):

    """

    Execution tier — lower tiers run first.

    실행 티어 — 낮은 티어가 먼저(레지스트리 순서).



    수정 시 주의점:

        String values are serialized in docs/logs — avoid renaming lightly.

    """



    IDENTITY = "identity"

    NARRATIVE = "narrative"

    TEMPORAL = "temporal"

    STRUCTURAL = "structural"

    MECHANISM = "mechanism"


