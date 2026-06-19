"""

Skeptic rule engine — run codified rules and aggregate verdicts.

스케ptic 규칙 엔진 — 코딩된 규칙을 실행하고 판정을 집계한다.



Purpose / 목적

--------------

Evaluate every directed causal hypothesis (source → target) against the full

rule registry, aggregate per-rule outcomes into accept/reject verdicts, and

emit verified ``CausalEdge`` objects for accepted pairs.

모든 방향성 인과 가설(원인 → 결과)에 대해 전체 규칙 레지스트리를 적용하고,

규칙별 결과를 수용/거부 판정으로 집계하며, 수용된 쌍에 대해 ``CausalEdge``를 생성한다.



Pipeline position / 파이프라인 위치

---------------------------------

  hypothesis.generate_pairwise_hypotheses  →  **SkepticEngine**  →  batch_filter

  → retry (INCONCLUSIVE)  →  node.skeptic_node (LangGraph state update)



Called after atomic facts are complete; upstream must not pass narrative fields

into ``AtomicFact`` — rules assume mechanical crumbs only.

원자 사실(completed_facts)이 준비된 뒤 호출된다. 상류에서 서술·감정 필드를

``AtomicFact``에 넣지 말 것 — 규칙은 기계적 크럼만 가정한다.



When to modify / 수정 시점

--------------------------

- Adding a new rule: register in ``rules/registry.py``; engine picks it up via

  ``DEFAULT_RULES`` — do **not** hard-code rule logic here.

- Changing accept/reject policy: edit ``aggregator.py``, not this file.

- Changing edge scoring: edit ``scoring.py``.

- 새 규칙 추가: ``rules/registry.py``에 등록 — 엔진은 ``DEFAULT_RULES``로 자동 반영.

- 수용/거부 정책 변경: ``aggregator.py`` 수정.

- 엣지 점수 변경: ``scoring.py`` 수정.



Key invariants / 핵심 불변조건

------------------------------

- ``evaluate_hypothesis``: ``accepted=True`` iff aggregator returns causal accept;

  ``verified_edge`` is non-None only when accepted.

- ``evaluate_batch``: always runs ``resolve_bidirectional_conflicts`` on verified

  edges (Rule 12 batch) before returning.

- Rule evaluation order is fixed by registry; engine does not reorder rules.

- ``evaluate_hypothesis``에서 ``accepted=True``이면 집계기가 인과 수용을 반환한 경우뿐;

  ``verified_edge``는 수용 시에만 non-None.

- ``evaluate_batch``는 반환 전 항상 양방향 충돌 해소(Rule 12)를 수행한다.

- 규칙 평가 순서는 레지스트리에 고정; 엔진은 재정렬하지 않는다.

"""



from __future__ import annotations



from deconstructor.models import AtomicFact, CausalEdge

from deconstructor.skeptic.aggregator import aggregate_verdict, first_rejection_reason

from deconstructor.skeptic.batch_filter import resolve_bidirectional_conflicts

from deconstructor.skeptic.hypothesis import facts_by_id, generate_pairwise_hypotheses

from deconstructor.skeptic.rules import DEFAULT_RULES

from deconstructor.skeptic.rules.base import SkepticRule

from deconstructor.skeptic.scoring import compute_latency_ms, compute_probability

from deconstructor.skeptic.schemas import (

    CausalClassification,

    CausalHypothesis,

    HypothesisVerdict,

    RejectedHypothesis,

    RuleCheckResult,

    RuleContext,

    RuleOutcome,

    SkepticBatchResult,

)





class SkepticEngine:

    """

    Run all codified rules on each hypothesis and batch-aggregate results.

    각 가설에 대해 코딩된 규칙을 모두 실행하고 배치 단위로 결과를 집계한다.



    Correlation vs causation is decided by explicit rules, not LLM narrative.

    상관 vs 인과 판별은 LLM 서술이 아니라 명시적 규칙으로만 결정된다.



    수정 시 주의점:

        - Custom ``rules`` list bypasses ``DEFAULT_RULES`` entirely; test coverage

          should mirror production registry order when injecting mocks.

        - Do not cache ``RuleContext`` across hypotheses — each pair is independent.

    """



    def __init__(self, rules: list[SkepticRule] | None = None) -> None:

        """

        Args:

            rules: Optional override of ``DEFAULT_RULES``. None → production registry.



        수정 시 주의점:

            Injecting a subset of rules changes aggregator truth-table expectations.

        """

        self._rules = rules if rules is not None else list(DEFAULT_RULES)



    def run_rules(self, ctx: RuleContext) -> list[RuleCheckResult]:

        """

        Evaluate every rule; return full rule trace.

        모든 규칙을 평가하고 전체 규칙 추적(trace)을 반환한다.



        Args:

            ctx: Frozen read-only context for one directed hypothesis.



        Returns:

            One ``RuleCheckResult`` per registered rule, in registry order.



        수정 시 주의점:

            Short-circuiting rules here would break audit/replay; always run all.

        """

        return [rule.evaluate(ctx) for rule in self._rules]



    def evaluate_hypothesis(

        self,

        hypothesis: CausalHypothesis,

        facts: dict[str, AtomicFact],

    ) -> HypothesisVerdict:

        """

        Run every rule on one hypothesis and aggregate.

        단일 가설에 대해 모든 규칙을 실행하고 집계한다.



        Args:

            hypothesis: Directed pair (source_fact_id → target_fact_id).

            facts: Id-indexed atomic facts; must contain both hypothesis endpoints.



        Returns:

            ``HypothesisVerdict`` with ``verified_edge`` populated only if accepted.



        수정 시 주의점:

            Missing fact ids raise KeyError by design — callers must pre-validate.

            Probability/latency on edges come from ``scoring`` helpers only here.

        """

        source = facts[hypothesis.source_fact_id]

        target = facts[hypothesis.target_fact_id]

        ctx = RuleContext(source=source, target=target, hypothesis=hypothesis)



        rule_results = self.run_rules(ctx)

        classification, accepted, _trace = aggregate_verdict(rule_results)



        verified_edge: CausalEdge | None = None

        if accepted:

            # Only accepted hypotheses become graph edges; scoring is post-aggregation.

            verified_edge = CausalEdge(

                source_fact_id=hypothesis.source_fact_id,

                target_fact_id=hypothesis.target_fact_id,

                probability=compute_probability(rule_results),

                latency=compute_latency_ms(source, target),

            )



        return HypothesisVerdict(

            hypothesis=hypothesis,

            rule_results=rule_results,

            final_classification=classification,

            accepted=accepted,

            verified_edge=verified_edge,

        )



    def evaluate_batch(

        self,

        facts: list[AtomicFact],

        *,

        mechanisms: dict[tuple[str, str], str] | None = None,

    ) -> SkepticBatchResult:

        """

        Evaluate all pairwise hypotheses for a fact set.

        사실 집합에 대해 모든 순서쌍 가설을 평가한다.



        Args:

            facts: Completed atomic facts (≥2 for non-empty hypothesis set).

            mechanisms: Optional ``(source_id, target_id) -> mechanism text`` map

                injected into hypotheses before rule evaluation (retry path).



        Returns:

            ``SkepticBatchResult`` with verified edges, rejections, and full verdicts.

            Bidirectional conflicts resolved on verified_edges only.



        수정 시 주의점:

            ``mechanisms`` keys must match ordered pair direction; undirected keys

            will not attach to hypotheses. Rejected list includes CORRELATION and

            INCONCLUSIVE — retry layer filters INCONCLUSIVE separately.

        """

        index = facts_by_id(facts)

        hypotheses = generate_pairwise_hypotheses(facts, mechanisms=mechanisms)



        verdicts = [self.evaluate_hypothesis(h, index) for h in hypotheses]



        verified: list[CausalEdge] = []

        rejected: list[RejectedHypothesis] = []



        for v in verdicts:

            if v.accepted and v.verified_edge is not None:

                verified.append(v.verified_edge)

            else:

                # Collect FAIL rule ids for debugging; reason from first FAIL with text.

                failed_ids = [

                    r.rule_id

                    for r in v.rule_results

                    if r.outcome == RuleOutcome.FAIL

                ]

                rejected.append(

                    RejectedHypothesis(

                        source_fact_id=v.hypothesis.source_fact_id,

                        target_fact_id=v.hypothesis.target_fact_id,

                        classification=v.final_classification,

                        failed_rule_ids=failed_ids,

                        reason=first_rejection_reason(v.rule_results),

                    )

                )



        # Rule 12 (batch): A→B and B→A cannot both survive — keep higher probability.

        verified = resolve_bidirectional_conflicts(verified)



        return SkepticBatchResult(

            verified_edges=verified,

            rejected=rejected,

            verdicts=verdicts,

        )


