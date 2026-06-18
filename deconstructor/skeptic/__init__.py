"""
The Skeptic — codified correlation vs causation verification.
The Skeptic — 코딩된 상관 vs 인과 검증.

Purpose / 목적
--------------
Package-level public API: engine, schemas, aggregator for external imports.
패키지 공개 API: 엔진, 스키마, 집계기.

Pipeline position / 파이프라인 위치
---------------------------------
  deconstructor.pipeline  →  skeptic.node  →  (this package)

When to modify / 수정 시점
--------------------------
- Extend ``__all__`` when adding stable public types used outside skeptic/.

Key invariants / 핵심 불변조건
------------------------------
- Rule logic lives in rules/ — not re-exported here by default.
"""

from deconstructor.skeptic.aggregator import aggregate_verdict
from deconstructor.skeptic.engine import SkepticEngine
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

__all__ = [
    "CausalClassification",
    "CausalHypothesis",
    "HypothesisVerdict",
    "RejectedHypothesis",
    "RuleCheckResult",
    "RuleContext",
    "RuleOutcome",
    "SkepticBatchResult",
    "SkepticEngine",
    "aggregate_verdict",
]
