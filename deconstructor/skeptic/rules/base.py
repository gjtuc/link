"""
Base protocol for codified skeptic rules.
코딩된 스케ptic 규칙 기본 프로토콜.

Purpose / 목적
--------------
Define ``SkepticRule`` protocol and shared text tokenization for mechanical
overlap checks across rule families.
``SkepticRule`` 프로토콜과 규칙 패밀리 공통 기계적 토큰화 정의.

Pipeline position / 파이프라인 위치
---------------------------------
  rules/* implementations  →  **SkepticRule.evaluate**  →  RuleCheckResult

When to modify / 수정 시점
--------------------------
- ``tokenize`` changes affect R05, R06, R07, R08, propagation helpers — regression test all.
- Rules must stay pure: no I/O, no mutation of ``RuleContext`` (frozen).

Key invariants / 핵심 불변조건
------------------------------
- Each rule exposes stable ``rule_id`` string matching registry / fixtures.
- ``evaluate`` returns exactly one ``RuleCheckResult`` per call.
- 규칙은 부수효과 없이 ``RuleContext``만 읽음.
"""

from __future__ import annotations

from typing import Protocol

from deconstructor.skeptic.schemas import RuleCheckResult, RuleContext


class SkepticRule(Protocol):
    """
    A single deterministic correlation-vs-causation check.
    단일 결정론적 상관-vs-인과 검사.

    수정 시 주의점:
        Implementations are classes with ``rule_id`` class attribute and ``evaluate`` method.
    """

    rule_id: str

    def evaluate(self, ctx: RuleContext) -> RuleCheckResult:
        """
        Run the rule against one hypothesis.
        한 가설에 대해 규칙 실행.

        Args:
            ctx: Frozen source, target, hypothesis.

        Returns:
            PASS, FAIL (with classification when rejecting), or ABSTAIN.

        수정 시 주의점:
            FAIL for correlation should set ``classification=CORRELATION`` for aggregator A1.
        """
        ...


def tokenize(text: str) -> set[str]:
    """
    Lowercase mechanical tokens from subject or state_change strings.
    subject·state_change 문자열에서 소문자 기계 토큰 집합 추출.

    Args:
        text: Raw crumb field text.

    Returns:
        Set of tokens length > 1 after punctuation normalization.

    수정 시 주의점:
        CJK text may not split well — narrative rule uses raw substring scan too.
        Changing delimiters affects jaccard thresholds in R05.
    """
    raw = text.replace("->", " ").replace("|", " ").replace("_", " ")
    for ch in ".,;:!?()[]{}":
        raw = raw.replace(ch, " ")
    return {t for t in raw.lower().split() if len(t) > 1}
