"""
Step 2 — Dreamer LLM 호출 (Micro-step S2-3)
============================================

Purpose / 목적
--------------
Flash·Pro 두 번의 structured LLM 호출로 Dreamer 2단계 파이프라인을 구현한다.

단계
----
  S2-3a  ``invoke_flash_breadth`` — tier=flash, ``DreamHypothesisBroadList`` (15~20)
  S2-3b  ``invoke_pro_compress`` — tier=pro, ``DreamHypothesisList`` (≤5)
  S2-3c  ``invoke_dream_hypotheses`` — a → b 오케스트레이션 (live 진입점)

입력 블록
---------
  ``format_source_facts_block`` — completed_facts id·subject·state_change
  ``format_candidates_block`` — Flash 후보 전체 (Pro 필터 입력)

When to modify
--------------
- 모델 tier 변경: ``deconstructor/llm/__init__.py`` ``get_chat_model(tier=...)``
- 개수 상한: ``schemas.FLASH_*`` / ``PRO_HYPOTHESIS_MAX`` · prompts 문구 동기화
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.agents.dreamer.prompts import (
    FLASH_BREADTH_SYSTEM,
    FLASH_BREADTH_USER,
    PRO_COMPRESS_SYSTEM,
    PRO_COMPRESS_USER,
)
from deconstructor.agents.dreamer.schemas import (
    DreamHypothesis,
    DreamHypothesisBroadList,
    DreamHypothesisList,
)
from deconstructor.llm import get_chat_model
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-3] {msg}"
    logger.info(line)
    print(line)


def format_source_facts_block(facts: list[AtomicFact]) -> str:
    """completed_facts → LLM 입력 블록."""
    lines: list[str] = []
    for fact in facts:
        ts = fact.timestamp.isoformat() if fact.timestamp else "n/a"
        lines.append(
            f"- id={fact.id} | subject={fact.subject!r} | "
            f"state_change={fact.state_change!r} | timestamp={ts} | "
            f"source_type={fact.source_type}"
        )
    return "\n".join(lines) if lines else "(none)"


def format_candidates_block(hypotheses: list[DreamHypothesis]) -> str:
    lines: list[str] = []
    for i, hyp in enumerate(hypotheses, 1):
        lag = hyp.lag_minutes if hyp.lag_minutes is not None else "n/a"
        lines.append(
            f"[{i}] source_fact_id={hyp.source_fact_id} | subject={hyp.subject!r} | "
            f"state_change={hyp.state_change!r} | lag_minutes={lag} | "
            f"mechanism={hyp.mechanism!r}"
        )
    return "\n".join(lines) if lines else "(none)"


def build_flash_breadth_messages(
    source_facts: list[AtomicFact],
    *,
    headline: str,
) -> list:
    facts_block = format_source_facts_block(source_facts)
    _log(f"build flash messages: {len(source_facts)} source fact(s)")
    return [
        SystemMessage(content=FLASH_BREADTH_SYSTEM),
        HumanMessage(
            content=FLASH_BREADTH_USER.format(
                facts_block=facts_block,
                headline=headline,
            )
        ),
    ]


def build_pro_compress_messages(
    source_facts: list[AtomicFact],
    candidates: list[DreamHypothesis],
    *,
    headline: str,
) -> list:
    facts_block = format_source_facts_block(source_facts)
    candidates_block = format_candidates_block(candidates)
    _log(
        f"build pro compress messages: sources={len(source_facts)} "
        f"candidates={len(candidates)}"
    )
    return [
        SystemMessage(content=PRO_COMPRESS_SYSTEM),
        HumanMessage(
            content=PRO_COMPRESS_USER.format(
                facts_block=facts_block,
                headline=headline,
                candidates_block=candidates_block,
            )
        ),
    ]


def invoke_flash_breadth(
    source_facts: list[AtomicFact],
    *,
    headline: str,
    llm: Any | None = None,
) -> DreamHypothesisBroadList:
    """Flash tier — 15~20 breadth hypotheses."""
    _log("invoke flash breadth DreamHypothesisBroadList")
    model = (
        llm
        if llm is not None
        else get_chat_model(tier="flash").with_structured_output(
            DreamHypothesisBroadList
        )
    )
    return model.invoke(build_flash_breadth_messages(source_facts, headline=headline))


def invoke_pro_compress(
    source_facts: list[AtomicFact],
    broad: DreamHypothesisBroadList,
    *,
    headline: str,
    llm: Any | None = None,
) -> DreamHypothesisList:
    """Pro tier — anchor, dedupe, ≤5 finalists."""
    _log(f"invoke pro compress from {len(broad.hypotheses)} flash candidate(s)")
    model = (
        llm
        if llm is not None
        else get_chat_model(tier="pro").with_structured_output(DreamHypothesisList)
    )
    return model.invoke(
        build_pro_compress_messages(
            source_facts,
            broad.hypotheses,
            headline=headline,
        )
    )


def invoke_dream_hypotheses(
    source_facts: list[AtomicFact],
    *,
    headline: str,
    llm: Any | None = None,
) -> DreamHypothesisList:
    """
    Live 2-stage Dreamer: Flash breadth → Pro compress.

    ``llm`` 인자는 단일 모델 mock 테스트용; 지정 시 flash·pro 모두 동일 인스턴스 사용.
    """
    _log("invoke 2-stage dreamer (flash breadth → pro compress)")
    flash_llm = llm
    pro_llm = llm
    broad = invoke_flash_breadth(source_facts, headline=headline, llm=flash_llm)
    _log(f"flash stage done: {len(broad.hypotheses)} candidate(s)")
    compressed = invoke_pro_compress(
        source_facts, broad, headline=headline, llm=pro_llm
    )
    _log(f"pro stage done: {len(compressed.hypotheses)} finalist(s)")
    return compressed
