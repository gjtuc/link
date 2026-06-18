"""
Micro-step aggregation policy for hypothesis verdicts.
가설 판정용 미세 단계(micro-step) 집계 정책.

Purpose / 목적
--------------
Convert an ordered list of ``RuleCheckResult`` into a single classification,
accept/reject flag, and auditable ``AggregationStep`` trace.
규칙 결과 리스트를 단일 분류·수용 여부·감사 가능한 집계 추적으로 변환한다.

Pipeline position / 파이프라인 위치
---------------------------------
  SkepticEngine.evaluate_hypothesis  →  **aggregate_verdict**  →  verdict / report

When to modify / 수정 시점
--------------------------
- Any change to accept/reject logic: update ``truth_table.py`` rows and tests.
- Policy is intentionally strict: first FAIL wins; unanimous PASS required.
- 집계 로직 변경 시 ``truth_table.py`` 및 테스트 동시 갱신 필수.

Key invariants / 핵심 불변조건
------------------------------
- A1: first FAIL with CORRELATION → reject correlation.
- A2/A3: first FAIL with INCONCLUSIVE or unclassified → reject that class.
- A4: all ABSTAIN → INCONCLUSIVE reject.
- A5: all decisive rules PASS → accept CAUSAL.
- A6: mixed PASS/ABSTAIN without FAIL still rejects INCONCLUSIVE (no partial credit).
- 첫 FAIL이 우선; 전원 PASS(ABSTAIN 제외)만 수용.
"""

from __future__ import annotations

from dataclasses import dataclass

from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleOutcome,
)


@dataclass(frozen=True)
class AggregationStep:
    """
    One micro-step in the aggregation decision tree.
    집계 결정 트리의 한 미세 단계.

    ``step_id`` matches truth-table labels (A1–A6).
    """

    step_id: str
    description: str
    outcome: str


def aggregate_verdict(
    rule_results: list[RuleCheckResult],
) -> tuple[CausalClassification, bool, list[AggregationStep]]:
    """
    Apply strict aggregation policy; return classification, accepted, trace.
    엄격한 집계 정책 적용; 분류, 수용 여부, 추적 반환.

    Policy order:
      A1. First FAIL classified as CORRELATION -> reject
      A2. First FAIL classified as INCONCLUSIVE -> reject
      A3. First FAIL without classification -> reject inconclusive
      A4. All ABSTAIN -> reject inconclusive
      A5. All decisive PASS -> accept causal
      A6. Mixed without FAIL -> reject inconclusive

    Args:
        rule_results: Full rule trace in registry evaluation order.

    Returns:
        Tuple of (final_classification, accepted, aggregation_trace).

    수정 시 주의점:
        Scan order is rule_results list order — registry order matters for "first FAIL".
        Do not treat ABSTAIN as PASS; only decisive (non-ABSTAIN) rules count for A5/A6.
    """
    trace: list[AggregationStep] = []

    # Phase 1: short-circuit on first FAIL (correlation or inconclusive).
    for result in rule_results:
        if result.outcome != RuleOutcome.FAIL:
            continue
        if result.classification == CausalClassification.CORRELATION:
            trace.append(
                AggregationStep(
                    "A1",
                    f"correlation fail at {result.rule_id}",
                    "REJECT_CORRELATION",
                )
            )
            return CausalClassification.CORRELATION, False, trace
        # Unclassified FAIL defaults to INCONCLUSIVE for A2/A3 labeling.
        cls = result.classification or CausalClassification.INCONCLUSIVE
        trace.append(
            AggregationStep(
                "A2" if cls == CausalClassification.INCONCLUSIVE else "A3",
                f"fail at {result.rule_id}",
                f"REJECT_{cls.value.upper()}",
            )
        )
        return cls, False, trace

    # Phase 2: no FAIL — inspect decisive vs abstaining rules.
    decisive = [r for r in rule_results if r.outcome != RuleOutcome.ABSTAIN]
    if not decisive:
        trace.append(AggregationStep("A4", "all rules abstained", "REJECT_INCONCLUSIVE"))
        return CausalClassification.INCONCLUSIVE, False, trace

    if all(r.outcome == RuleOutcome.PASS for r in decisive):
        trace.append(AggregationStep("A5", "unanimous pass", "ACCEPT_CAUSAL"))
        return CausalClassification.CAUSAL, True, trace

    # PASS + ABSTAIN mix without FAIL — still not unanimous decisive pass.
    trace.append(AggregationStep("A6", "mixed without unanimous pass", "REJECT_INCONCLUSIVE"))
    return CausalClassification.INCONCLUSIVE, False, trace


def first_rejection_reason(rule_results: list[RuleCheckResult]) -> str:
    """
    Pick the first non-empty reason from a FAIL rule for human-readable rejections.
    FAIL 규칙 중 첫 번째 비어 있지 않은 reason을 거부 사유로 선택.

    Args:
        rule_results: Rule trace from one hypothesis evaluation.

    Returns:
        First FAIL ``reason`` string, or fallback ``"no decisive causal evidence"``.

    수정 시 주의점:
        Only FAIL outcomes count; ABSTAIN-heavy rejects use the fallback message.
    """
    for result in rule_results:
        if result.outcome == RuleOutcome.FAIL and result.reason:
            return result.reason
    return "no decisive causal evidence"
