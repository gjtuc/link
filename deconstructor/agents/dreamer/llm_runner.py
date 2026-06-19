"""
Step 2 — Dreamer LLM 호출 (Micro-step S2-3)
============================================
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.agents.dreamer.prompts import DREAMER_SYSTEM, DREAMER_USER
from deconstructor.agents.dreamer.schemas import DreamHypothesisList
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


def build_dreamer_messages(
    source_facts: list[AtomicFact],
    *,
    headline: str,
) -> list:
    facts_block = format_source_facts_block(source_facts)
    _log(f"build messages: {len(source_facts)} source fact(s)")
    return [
        SystemMessage(content=DREAMER_SYSTEM),
        HumanMessage(
            content=DREAMER_USER.format(
                facts_block=facts_block,
                headline=headline,
            )
        ),
    ]


def invoke_dream_hypotheses(
    source_facts: list[AtomicFact],
    *,
    headline: str,
    llm: Any | None = None,
) -> DreamHypothesisList:
    """Live LLM structured output → DreamHypothesisList."""
    _log("invoke live LLM structured DreamHypothesisList")
    model = (
        llm
        if llm is not None
        else get_chat_model().with_structured_output(DreamHypothesisList)
    )
    return model.invoke(build_dreamer_messages(source_facts, headline=headline))
