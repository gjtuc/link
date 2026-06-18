"""Phase 1 — Pydantic atomic boxes."""

from __future__ import annotations

from pydantic import ValidationError

from deconstructor.models import AtomicFact, CausalEdge, FactList
from tests.smoke.harness import StepRunner


def phase_1_pydantic(run: StepRunner) -> None:
    run.section("1a AtomicFact fields")

    fact = AtomicFact(
        subject="grid",
        state_change="power -> off",
        is_atomic=True,
        reasoning="indivisible",
    )
    run.check("subject stored", fact.subject == "grid")
    run.check("is_atomic stored", fact.is_atomic is True)
    run.check("uuid id generated", len(fact.id) >= 32)

    run.section("1b AtomicFact validation rejects")

    try:
        AtomicFact(subject="", state_change="a -> b")
        run.check("empty subject rejected", False)
    except ValidationError:
        run.check("empty subject rejected", True)

    try:
        AtomicFact(subject="x", state_change="")
        run.check("empty state_change rejected", False)
    except ValidationError:
        run.check("empty state_change rejected", True)

    run.section("1c FactList schema")

    batch = FactList(facts=[fact])
    run.check("facts length", len(batch.facts) == 1)

    try:
        FactList(facts=[])
        run.check("empty facts list rejected", False)
    except ValidationError:
        run.check("empty facts list rejected", True)

    run.section("1d CausalEdge bounds")

    edge = CausalEdge(
        source_fact_id=fact.id,
        target_fact_id="other",
        probability=0.5,
        latency=100,
    )
    run.check("probability in range", 0.0 <= edge.probability <= 1.0)

    try:
        CausalEdge(source_fact_id="a", target_fact_id="b", probability=2.0)
        run.check("probability>1 rejected", False)
    except ValidationError:
        run.check("probability>1 rejected", True)

    run.section("1e JSON round-trip")

    raw = fact.model_dump_json()
    restored = AtomicFact.model_validate_json(raw)
    run.check("round-trip subject", restored.subject == fact.subject)
    run.check("round-trip id", restored.id == fact.id)
