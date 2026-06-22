"""LangGraph shared State TypedDict for the deconstructor pipeline.
디컨스트럭터 파이프라인 LangGraph 공유 State TypedDict.

Purpose / 목적
--------------
Defines the **single source of truth** for all keys flowing through
deconstruct → verify → skeptic → weaver nodes. Uses ``Annotated[..., operator.add]``
on ``completed_facts`` so LangGraph merges incremental completions.
deconstruct → verify → skeptic → weaver 노드가 공유하는 **키의 단일 정의**.
``completed_facts``는 ``operator.add``로 증분 완료를 병합.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    state_factory.make_initial_state()
        --> graph nodes read/write State fields
        --> final State --> report / json_export / weaver

Every graph node return value must be a partial dict compatible with these keys.
모든 노드 반환은 이 키와 호환되는 partial dict여야 함.

Field guide / 필드 가이드
-------------------------
- ``raw_text``: original headline/input (immutable after init).
- ``extracted_facts``: current decomposition queue (non-atomic crumbs).
- ``completed_facts``: accumulated atomic facts (reducer: add).
- ``recursion_depth`` / ``max_recursion_depth``: deconstruct loop control.
- ``partial_run`` / ``partial_run_reason``: set when depth cap hits with leftovers.
- ``verified_edges`` / ``rejected_hypotheses`` / ``skeptic_verdicts``: skeptic outputs.
- ``inferred_facts`` / ``dreamer_log``: Dreamer agent outputs (Step 2).
- ``promoted_facts`` / ``dropped_hypotheses`` / ``fact_checker_log``: Fact-Checker (Step 3).
- ``enable_dreamer``: CLI ``--enable-dreamer`` — dreamer→fact_checker 경로 활성.
- ``verified_edges_pass1`` / ``pass2_gap_nodes``: Q1 2-pass Dreamer pass-1 outputs.
- ``weaver_result``: final persistence summary.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Adding a key requires: factory default, any node that writes it, report section
  or trace handler, and migration notes for saved JSON snapshots.
- Only ``completed_facts`` uses a reducer; other list fields are typically replaced
  wholesale per node update — confirm LangGraph merge behavior before changing.
- 키 추가 = factory 기본값 + 쓰는 노드 + report/trace + JSON 스냅샷 호환.
- reducer는 ``completed_facts``만; 다른 리스트는 노드 update로 통째 교체되는 경우 많음.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.agents.fact_checker.schemas import DroppedHypothesis
from deconstructor.skeptic.run_log import SkepticLogEntry
from deconstructor.skeptic.schemas import HypothesisVerdict, RejectedHypothesis
from deconstructor.weaver.schemas import WeaverResult


class State(TypedDict):
    """Shared LangGraph state for deconstruct, verify, skeptic, and weaver.
    deconstruct·verify·skeptic·weaver가 공유하는 LangGraph state."""

    raw_text: str
    extracted_facts: list[AtomicFact]
    # Reducer: each verify pass appends newly completed atoms.
    # Reducer: verify 패스마다 새로 완료된 원자 append.
    completed_facts: Annotated[list[AtomicFact], operator.add]
    recursion_depth: int
    max_recursion_depth: int
    partial_run: bool
    partial_run_reason: str
    skeptic_log: list[SkepticLogEntry]
    verified_edges: list[CausalEdge]
    rejected_hypotheses: list[RejectedHypothesis]
    skeptic_verdicts: list[HypothesisVerdict]
    inferred_facts: list[AtomicFact]
    dreamer_log: list[str]
    promoted_facts: Annotated[list[AtomicFact], operator.add]
    dropped_hypotheses: list[DroppedHypothesis]
    fact_checker_log: list[str]
    enable_dreamer: bool
    verified_edges_pass1: list[CausalEdge]
    pass2_gap_nodes: list[dict]
    skeptic_pass1_log: list[SkepticLogEntry]
    analysis_run_id: str
    source_document_meta: dict[str, str | int]
    corpus_fact_pool: list[AtomicFact]
    weaver_result: WeaverResult | None
