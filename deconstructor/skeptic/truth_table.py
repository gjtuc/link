"""
Aggregator ABSTAIN / PASS / FAIL truth table generator.
집계기 ABSTAIN / PASS / FAIL 진리표 생성기.

Purpose / 목적
--------------
Synthetic rule-outcome patterns → expected aggregator step (A1–A6) for regression
tests. Guards ``aggregator.aggregate_verdict`` against silent policy drift.
합성 규칙 결과 패턴 → 집계 단계(A1–A6) 기대값으로 회귀 테스트.
``aggregate_verdict`` 정책 드리프트 방지.

Pipeline position / 파이프라인 위치
---------------------------------
  Test/dev utility — imported by skeptic tests, not production node path.
  테스트·개발 유틸 — 프로덕션 노드 경로 아님.

When to modify / 수정 시점
--------------------------
- When aggregator policy changes: update ``build_core_truth_table`` rows first.
- ``build_abstain_combination_table`` exhausts PASS/ABSTAIN combos for 3 slots.
- 집계 정책 변경 시 ``build_core_truth_table`` 행을 먼저 갱신.

Key invariants / 핵심 불변조건
------------------------------
- Pattern chars: P=PASS, F=FAIL(correlation), I=INCONCLUSIVE fail, U=unclassified fail, A=ABSTAIN.
- ``verify_truth_table`` returns empty list on full match.
- 패턴 문자 의미 고정; 검증 실패 시 오류 메시지 리스트 반환.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from deconstructor.skeptic.aggregator import aggregate_verdict
from deconstructor.skeptic.schemas import (
    CausalClassification,
    RuleCheckResult,
    RuleOutcome,
)


@dataclass(frozen=True)
class TruthTableRow:
    """
    One synthetic outcome pattern and expected aggregator result.
    합성 결과 패턴 하나와 기대 집계 결과.
    """

    pattern: str
    expected_step: str
    expected_accepted: bool
    expected_classification: CausalClassification


def _results_from_pattern(pattern: str) -> list[RuleCheckResult]:
    """
    Map a pattern string (P/F/I/U/A per rule slot) to RuleCheckResults.
    패턴 문자열(규칙 슬롯당 P/F/I/U/A)을 RuleCheckResult 리스트로 변환.

    Args:
        pattern: One char per synthetic rule, e.g. ``"PPP"``, ``"F"``.

    Returns:
        List of synthetic ``RuleCheckResult`` for ``aggregate_verdict``.

    수정 시 주의점:
        Single-char patterns simulate "first rule decides" paths for A1–A3.
    """
    mapping = {
        "P": RuleCheckResult(rule_id="T", outcome=RuleOutcome.PASS),
        "F": RuleCheckResult(
            rule_id="T_FAIL",
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.CORRELATION,
            reason="synthetic fail",
        ),
        "I": RuleCheckResult(
            rule_id="T_INC",
            outcome=RuleOutcome.FAIL,
            classification=CausalClassification.INCONCLUSIVE,
            reason="synthetic inconclusive",
        ),
        "U": RuleCheckResult(
            rule_id="T_UNC",
            outcome=RuleOutcome.FAIL,
            classification=None,
            reason="unclassified fail",
        ),
        "A": RuleCheckResult(rule_id="T_ABS", outcome=RuleOutcome.ABSTAIN),
    }
    return [mapping[ch] for ch in pattern]


def build_core_truth_table() -> list[TruthTableRow]:
    """
    T13-1: Enumerate decisive aggregator paths (not full 3^n explosion).
    T13-1: 결정적 집계 경로 열거(전체 3^n 폭발 아님).

    Patterns use up to 3 rule slots: correlation fail wins (A1), then
    inconclusive fail (A2), unclassified (A3), all abstain (A4), pass (A5),
    mixed pass+abstain without fail (A6).

    Returns:
        Canonical rows covering each aggregation branch once.

    수정 시 주의점:
        Must stay in sync with ``aggregate_verdict`` step_id strings.
    """
    rows = [
        TruthTableRow("F", "A1", False, CausalClassification.CORRELATION),
        TruthTableRow("I", "A2", False, CausalClassification.INCONCLUSIVE),
        TruthTableRow("U", "A2", False, CausalClassification.INCONCLUSIVE),
        TruthTableRow("AAA", "A4", False, CausalClassification.INCONCLUSIVE),
        TruthTableRow("PPP", "A5", True, CausalClassification.CAUSAL),
        TruthTableRow("PAP", "A5", True, CausalClassification.CAUSAL),
        TruthTableRow("PA", "A5", True, CausalClassification.CAUSAL),
    ]
    return rows


def build_abstain_combination_table() -> list[TruthTableRow]:
    """
    T13-2: All combinations of PASS/ABSTAIN only (no FAIL) for 3 rules.
    T13-2: FAIL 없이 PASS/ABSTAIN만 3규칙 조합 전체.

    With only PASS and ABSTAIN, any decisive rule is PASS — unanimous accept (A5).
    All-ABSTAIN maps to A4.

    Returns:
        Eight rows (2^3 product of P/A).

    수정 시 주의점:
        Adding FAIL to this table would duplicate core table coverage.
    """
    rows: list[TruthTableRow] = []
    for combo in product("PA", repeat=3):
        pattern = "".join(combo)
        decisive_chars = [c for c in pattern if c != "A"]
        if not decisive_chars:
            # AAA → no decisive rules → A4.
            rows.append(
                TruthTableRow(pattern, "A4", False, CausalClassification.INCONCLUSIVE)
            )
        else:
            # Any PASS among decisive → all decisive are PASS → A5.
            rows.append(
                TruthTableRow(pattern, "A5", True, CausalClassification.CAUSAL)
            )
    return rows


def verify_truth_table(rows: list[TruthTableRow]) -> list[str]:
    """
    Return list of failure messages; empty means all pass.
    실패 메시지 리스트 반환; 비어 있으면 전부 통과.

    Args:
        rows: Expected pattern → aggregation outcomes.

    Returns:
        Human-readable mismatch strings; empty if aggregator matches all rows.

    수정 시 주의점:
        Compares last trace step_id only — multi-step traces not used in core table.
    """
    errors: list[str] = []
    for row in rows:
        results = _results_from_pattern(row.pattern)
        cls, accepted, trace = aggregate_verdict(results)
        step = trace[-1].step_id if trace else "?"
        if step != row.expected_step:
            errors.append(f"{row.pattern}: step {step} != {row.expected_step}")
        if accepted != row.expected_accepted:
            errors.append(f"{row.pattern}: accepted {accepted}")
        if cls != row.expected_classification:
            errors.append(f"{row.pattern}: class {cls}")
    return errors

