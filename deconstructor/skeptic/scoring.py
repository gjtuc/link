"""

Probability and latency scoring for verified edges.

검증된 엣지의 확률·지연(latency) 점수 산출.



Purpose / 목적

--------------

Attach quantitative metadata to accepted ``CausalEdge`` objects after aggregation.

Does not influence accept/reject — informational for graph ranking and UI.

집계 후 수용된 ``CausalEdge``에 정량 메타데이터를 부여한다.

수용/거부 판정에는 영향 없음 — 그래프 순위·UI용.



Pipeline position / 파이프라인 위치

---------------------------------

  aggregate_verdict (accept)  →  **compute_probability / compute_latency_ms**  →  CausalEdge



When to modify / 수정 시점

--------------------------

- Probability formula change affects bidirectional conflict tie-breaks in batch_filter.

- Latency uses source/target timestamps only — timezone-naive datetimes assumed aligned.

- 확률 공식 변경 시 batch_filter 동률 처리에 영향. 타임스탬프는 동일 타임존 가정.



Key invariants / 핵심 불변조건

------------------------------

- ABSTAIN rules excluded from probability denominator.

- Latency None when either timestamp missing; otherwise non-negative milliseconds.

- ABSTAIN은 확률 분모에서 제외. 타임스탬프 없으면 latency는 None.

"""



from __future__ import annotations



from deconstructor.models import AtomicFact

from deconstructor.skeptic.schemas import RuleCheckResult, RuleOutcome





def compute_probability(rule_results: list[RuleCheckResult]) -> float:

    """

    Ratio of PASS among decisive (non-ABSTAIN) rules.

    결정적(ABSTAIN 제외) 규칙 중 PASS 비율.



    Args:

        rule_results: Full rule trace for one accepted hypothesis.



    Returns:

        Float in [0, 1], rounded to 4 decimal places; 0.0 if no decisive rules.



    수정 시 주의점:

        Used for Rule 12 batch tie-break — changing formula changes surviving direction.

    """

    decisive = [r for r in rule_results if r.outcome != RuleOutcome.ABSTAIN]

    if not decisive:

        return 0.0

    passes = sum(1 for r in decisive if r.outcome == RuleOutcome.PASS)

    return round(passes / len(decisive), 4)





def compute_latency_ms(source: AtomicFact, target: AtomicFact) -> int | None:

    """

  Compute effect-minus-cause latency in milliseconds.

  원인→결과 시간 차이를 밀리초로 계산.



    Args:

        source: Hypothesized cause fact.

        target: Hypothesized effect fact.



    Returns:

        Non-negative ms if both timestamps exist; None otherwise.

        Negative deltas clamped to 0 (should not occur if temporal rules passed).



    수정 시 주의점:

        Does not re-validate temporal ordering — engine only calls on accepted pairs.

    """

    if source.timestamp is None or target.timestamp is None:

        return None

    delta = target.timestamp - source.timestamp

    return max(0, int(delta.total_seconds() * 1000))


