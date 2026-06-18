"""Phase 7 — Package split verification."""

from __future__ import annotations

from tests.smoke.harness import StepRunner
from tests.smoke.state import base_state


def phase_7_package_split(run: StepRunner) -> None:
    run.section("7a deconstruct subpackage")

    from deconstructor.deconstruct.apply import apply_deconstruct_result
    from deconstructor.deconstruct.input import resolve_stub_target
    from deconstructor.deconstruct.prompts import DECONSTRUCT_SYSTEM

    run.check("prompts module", "mechanical text decomposer" in DECONSTRUCT_SYSTEM.lower())
    run.check("resolve_stub_target", resolve_stub_target(base_state()) is not None)
    run.check("apply module callable", callable(apply_deconstruct_result))

    run.section("7b verify subpackage")

    from deconstructor.verify.partition import partition_by_atomicity

    a, n = partition_by_atomicity([])
    run.check("partition empty", a == [] and n == [])

    run.section("7c routing subpackage")

    from deconstructor.routing.after_verify import route_after_verify as rav

    run.check("routing import", rav(base_state(recursion_depth=1)) == "skeptic")

    run.section("7d graph.builder compiles")

    from deconstructor.graph.builder import build_graph

    g = build_graph(dry_run=True, persist_db=False)
    run.check("graph compiles", "deconstruct" in g.get_graph().nodes)
    run.check("weaver in graph", "weaver" in g.get_graph().nodes)
