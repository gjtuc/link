"""

Pydantic schemas for The Skeptic — causal vs correlational classification.

The Skeptic용 Pydantic 스키마 — 인과 vs 상관 분류.



Purpose / 목적

--------------

Define the typed contract between rules, engine, retry, and pipeline state.

No emotion or valuation fields — only mechanical verdict metadata.

규칙·엔진·재시도·파이프라인 state 간 타입 계약을 정의한다.

감정·평가 필드 없이 기계적 판정 메타데이터만 포함한다.



Pipeline position / 파이프라인 위치

---------------------------------

  Shared across rules/*, engine, aggregator, retry, node, report.

  모든 skeptic 하위 모듈이 import하는 공통 데이터 모델.



When to modify / 수정 시점

--------------------------

- New ``CausalClassification`` value: update aggregator policy + truth_table tests.

- New fields on verdict models: ensure JSON serialization in pipeline logs.

- ``RuleContext`` is frozen — add fields only if all rules need them read-only.

- 분류 enum 추가 시 집계기·truth_table 동시 수정. ``RuleContext``는 frozen 유지.



Key invariants / 핵심 불변조건

------------------------------

- ``RuleOutcome.FAIL`` may carry ``classification``; PASS/ABSTAIN typically do not.

- ``accepted`` on ``HypothesisVerdict`` mirrors aggregator boolean, not edge presence alone.

- ``verified_edge`` is optional and only set when accepted by engine.

- FAIL 시에만 ``classification`` 부여가 일반적. ``accepted``는 집계기 결과와 일치.

"""



from __future__ import annotations



from enum import Enum



from pydantic import BaseModel, Field



from deconstructor.models import AtomicFact, CausalEdge





class RuleOutcome(str, Enum):

    """

    Result of a single deterministic rule check.

    단일 결정론적 규칙 검사 결과.



    PASS: rule satisfied. FAIL: rule violated (often correlation).

    ABSTAIN: insufficient data — rule declines to decide.

  """



    PASS = "pass"

    FAIL = "fail"

    ABSTAIN = "abstain"





class CausalClassification(str, Enum):

    """

    Final mechanical classification for a hypothesis.

    가설에 대한 최종 기계적 분류.



    CAUSAL: accepted direct link. CORRELATION: rejected as spurious.

    INCONCLUSIVE: rejected but retry-eligible (mechanism fill path).

    """



    CAUSAL = "causal"

    CORRELATION = "correlation"

    INCONCLUSIVE = "inconclusive"





class CausalHypothesis(BaseModel):

    """

    A candidate directed link between two atomic facts.

    두 원자 사실 사이의 방향성 후보 연결.



    ``proposed_mechanism`` is optional mechanical text (e.g. from a later LLM pass).

    ``proposed_mechanism``은 선택적 기계적 전파 경로 문구(재시도·LLM 경로).



    수정 시 주의점:

        Empty mechanism is valid; mechanism rules ABSTAIN or infer from crumbs.

    """



    source_fact_id: str

    target_fact_id: str

    proposed_mechanism: str = Field(

        default="",

        description="Stated physical propagation path, if any.",

    )





class RuleCheckResult(BaseModel):

    """

    Output of one codified skeptic rule.

    코딩된 스케ptic 규칙 하나의 출력.



    수정 시 주의점:

        On FAIL, set ``classification`` when aggregator should branch (A1/A2/A3).

        ``reason`` is for logs/reports — keep mechanical, no sentiment.

    """



    rule_id: str

    outcome: RuleOutcome

    classification: CausalClassification | None = Field(

        default=None,

        description="Set when outcome is FAIL — usually CORRELATION.",

    )

    reason: str = Field(

        default="",

        description="Mechanical explanation; no sentiment.",

    )





class HypothesisVerdict(BaseModel):

    """

    Aggregated verdict after all rules run on one hypothesis.

    한 가설에 모든 규칙 적용 후 집계된 판정.



    수정 시 주의점:

        ``rule_results`` length must equal rule registry count for full traces.

    """



    hypothesis: CausalHypothesis

    rule_results: list[RuleCheckResult]

    final_classification: CausalClassification

    accepted: bool

    verified_edge: CausalEdge | None = None





class RejectedHypothesis(BaseModel):

    """

    A hypothesis rejected as correlation or inconclusive.

    상관 또는 미결정으로 거부된 가설.



    ``failed_rule_ids``: all rules that returned FAIL (may be empty if all ABSTAIN).

    """



    source_fact_id: str

    target_fact_id: str

    classification: CausalClassification

    failed_rule_ids: list[str] = Field(default_factory=list)

    reason: str = ""





class SkepticBatchResult(BaseModel):

    """

    Full output of one skeptic pass over a fact set.

    한 번의 스케ptic 패스 전체 출력.



    ``verdicts`` includes every ordered pair; ``verified_edges`` is accepted subset

    after batch conflict resolution.

    """



    verified_edges: list[CausalEdge] = Field(default_factory=list)

    rejected: list[RejectedHypothesis] = Field(default_factory=list)

    verdicts: list[HypothesisVerdict] = Field(default_factory=list)





class RuleContext(BaseModel):

    """

    Read-only inputs shared by every rule.

    모든 규칙이 공유하는 읽기 전용 입력.



    Frozen to prevent rules from mutating shared state during evaluation.

    평가 중 공유 상태 변조 방지를 위해 frozen.



    수정 시 주의점:

        Adding fields requires updating every rule's evaluate signature indirectly

        via ctx attribute access — prefer helpers in propagation.py when possible.

    """



    source: AtomicFact

    target: AtomicFact

    hypothesis: CausalHypothesis



    model_config = {"frozen": True}


