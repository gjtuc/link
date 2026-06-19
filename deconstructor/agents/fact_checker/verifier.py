"""
Step 3 — Verifier LLM (Micro-step CHECK-S3)
============================================
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from deconstructor.agents.fact_checker.prompts import VERIFIER_SYSTEM, VERIFIER_USER
from deconstructor.agents.fact_checker.schemas import SearchSnippet, VerificationVerdict
from deconstructor.llm import get_chat_model
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S3] {msg}"
    logger.info(line)
    print(line)


def format_snippets_block(snippets: list[SearchSnippet]) -> str:
    if not snippets:
        return "(no search results)"
    lines: list[str] = []
    for i, snip in enumerate(snippets, 1):
        lines.append(f"[{i}] {snip.title}\n{snip.content[:500]}")
    return "\n\n".join(lines)


def build_verifier_messages(
    fact: AtomicFact,
    snippets: list[SearchSnippet],
) -> list:
    ts = fact.timestamp.isoformat() if fact.timestamp else "n/a"
    return [
        SystemMessage(content=VERIFIER_SYSTEM),
        HumanMessage(
            content=VERIFIER_USER.format(
                subject=fact.subject,
                state_change=fact.state_change,
                timestamp=ts,
                mechanism=fact.reasoning or "n/a",
                snippets_block=format_snippets_block(snippets),
            )
        ),
    ]


def verify_hypothesis_with_llm(
    fact: AtomicFact,
    snippets: list[SearchSnippet],
    *,
    llm: Any | None = None,
) -> VerificationVerdict:
    """Live LLM verifier — snippets vs hypothesis."""
    _log(f"verify LLM subject={fact.subject!r} snippets={len(snippets)}")
    if not snippets:
        return VerificationVerdict(
            accepted=False,
            reason="no search snippets returned — drop",
        )

    model = (
        llm
        if llm is not None
        else get_chat_model().with_structured_output(VerificationVerdict)
    )
    return model.invoke(build_verifier_messages(fact, snippets))
