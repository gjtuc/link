"""

Canned fact-pair scenarios for skeptic micro-tests.

스케ptic 마이크로 테스트용 정형 사실 쌍 시나리오.



Purpose / 목적

--------------

Provide reproducible ``AtomicFact`` pairs with expected accept/fail rule ids

for unit/integration tests of the full rule stack.

전체 규칙 스택 단위·통합 테스트용 재현 가능한 ``AtomicFact`` 쌍과

기대 수용/실패 rule id 제공.



Pipeline position / 파이프라인 위치

---------------------------------

  tests  →  **PAIR_SCENARIOS**  →  SkepticEngine.evaluate_hypothesis



When to modify / 수정 시점

--------------------------

- Add scenario when new rule needs regression coverage — update ``expect_fail_rule``.

- Changing ``T0`` baseline shifts temporal rules — update all dependent timestamps.

- 규칙 추가 시 시나리오·``expect_fail_rule`` 동시 갱신.



Key invariants / 핵심 불변조건

------------------------------

- Each ``PairScenario`` is one directed (source → target) hypothesis.

- ``expect_accepted`` must match engine outcome with empty mechanism unless set.

- All facts ``is_atomic=True`` — matches pipeline completed_facts shape.

"""



from __future__ import annotations



from dataclasses import dataclass

from datetime import datetime, timedelta



from deconstructor.models import AtomicFact



T0 = datetime(2026, 6, 1, 10, 0, 0)





@dataclass(frozen=True)

class PairScenario:

    """

    Expected outcome for one directed hypothesis.

    단일 방향 가설에 대한 기대 결과.



    Args (fields):

        label: Human-readable scenario name for test ids.

        source: Cause crumb.

        target: Effect crumb.

        mechanism: Optional proposed_mechanism text (default scenarios use "").

        expect_accepted: Whether aggregator should accept as CAUSAL.

        expect_fail_rule: First FAIL rule_id if rejected; None if accepted.



    수정 시 주의점:

        ``expect_fail_rule`` is documentary — tests should assert engine behavior.

    """



    label: str

    source: AtomicFact

    target: AtomicFact

    mechanism: str

    expect_accepted: bool

    expect_fail_rule: str | None = None





def _f(

    id: str, subject: str, change: str, *, ts: datetime | None = None

) -> AtomicFact:

    """

    Factory for catalog ``AtomicFact`` rows.

    카탈로그용 ``AtomicFact`` 행 팩토리.



    Args:

        id: Short stable fact id for scenarios.

        subject: Entity/subject field.

        change: state_change field.

        ts: Optional timestamp for temporal rules.



    Returns:

        Atomic fact with ``is_atomic=True``.



    수정 시 주의점:

        Short ids (e.g. "g") are fine for tests — not production UUID style.

    """

    return AtomicFact(

        id=id,

        subject=subject,

        state_change=change,

        timestamp=ts,

        is_atomic=True,

    )





# --- Canonical crumbs shared across scenarios ---

GRID = _f("g", "grid", "power -> off", ts=T0)

MOTOR = _f("m", "motor", "power_supply -> interrupted", ts=T0 + timedelta(minutes=2))

WEATHER = _f("w", "weather", "temperature -> high", ts=T0)

PLANT_A = _f("a", "plant_a", "output -> zero", ts=T0)

PLANT_B = _f("b", "plant_b", "output -> zero", ts=T0)

PUMP = _f("p", "pump", "state -> running", ts=T0)

PUMP_STOP = _f("p2", "pump", "state -> stopped", ts=T0 + timedelta(seconds=10))

NARRATIVE = _f("n", "stock", "price -> bullish_spike", ts=T0)

SIM_SRC = _f("s1", "sensor_a", "reading -> high", ts=T0)

SIM_TGT = _f("s2", "sensor_b", "reading -> high", ts=T0)





PAIR_SCENARIOS: tuple[PairScenario, ...] = (

    # Ordered chain: grid power loss before motor interruption — propagation tokens.

    PairScenario("causal_grid_motor", GRID, MOTOR, "", True),

    # Unrelated domain, no shared tokens — R09 isolation.

    PairScenario("correlation_weather", GRID, WEATHER, "", False, "R09_CROSS_DOMAIN_ISOLATION"),

    # Same fact id — R01 (hypothesis gen normally skips; tests inject directly).

    PairScenario("self_loop", GRID, GRID, "", False, "R01_NO_SELF_LOOP"),

    # Parallel plant outputs at T0 — R05 common cause.

    PairScenario("common_cause_parallel", PLANT_A, PLANT_B, "", False, "R05_COMMON_CAUSE_PATTERN"),

    # Same entity ordered states — R10 chain + temporal pass.

    PairScenario("entity_chain", PUMP, PUMP_STOP, "", True),

    # Banned narrative token in source — R08.

    PairScenario("narrative_leak", NARRATIVE, MOTOR, "", False, "R08_NARRATIVE_LEAK"),

    # Equal timestamps, no mechanism — R04 simultaneity.

    PairScenario("simultaneous", SIM_SRC, SIM_TGT, "", False, "R04_SIMULTANEOUS_COOCCURRENCE"),

)


