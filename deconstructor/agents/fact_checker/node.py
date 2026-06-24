"""
Step 3 — Fact-Checker LangGraph 노드 (Micro-step CHECK-S3-node)
================================================================

Purpose / 목적
--------------
Dreamer ``inferred_facts``(≤5) 각각에 대해 웹 검색 + LLM Verifier로 promote/drop.

Live 경로 (TAVILY_API_KEY 설정 시)
----------------------------------
  build_search_query → TavilySearchProvider → verify_hypothesis_with_llm
  → promote_fact (check_status=promoted) | drop_fact (dropped_hypotheses)

Dry-run (키 없음)
-----------------
  stub_verify_hypothesis — 키워드 휴리스틱, **실제 웹 검증 아님**

Pipeline position
-----------------
  dreamer → **fact_checker** → skeptic → weaver
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deconstructor.agents.fact_checker.apply import drop_fact, promote_fact
from deconstructor.agents.fact_checker.corpus import collect_corpus_pool, corpus_verify_hypothesis
from deconstructor.agents.fact_checker.query_builder import build_search_query
from deconstructor.agents.fact_checker.schemas import DroppedHypothesis
from deconstructor.agents.fact_checker.search.factory import get_search_provider
from deconstructor.agents.fact_checker.stub import stub_verify_hypothesis
from deconstructor.agents.fact_checker.verifier import verify_hypothesis_with_llm
from deconstructor.print_util import safe_print
from deconstructor.models import AtomicFact
from deconstructor.web.progress_ctx import progress_sub

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[CHECK-S3-node] {msg}"
    logger.info(line)
    safe_print(line)


def _check_one_hypothesis(
    fact: AtomicFact,
    *,
    mode: str = "stub",
    dry_run: bool | None = None,
    search_provider=None,
    llm=None,
    corpus_pool: list[AtomicFact] | None = None,
) -> tuple[AtomicFact | None, DroppedHypothesis | None, list[str]]:
    """가설 1건 검증 → promote 또는 drop."""
    if dry_run is not None:
        mode = "stub" if dry_run else "live"

    logs: list[str] = []
    logs.append(
        f"[CHECK-S3-node] checking id={fact.id[:8]}.. subject={fact.subject!r} mode={mode}"
    )

    if mode == "corpus":
        pool = corpus_pool or []
        verdict = corpus_verify_hypothesis(fact, pool)
    elif mode == "stub":
        verdict = stub_verify_hypothesis(fact)
    else:
        provider = search_provider or get_search_provider()
        query = build_search_query(fact)
        snippets = provider.search(query)
        verdict = verify_hypothesis_with_llm(fact, snippets, llm=llm)

    if verdict.accepted:
        promoted = promote_fact(fact, verdict)
        msg = f"[CHECK-S3-PROMOTE] {fact.subject!r}: {verdict.reason}"
        safe_print(msg)
        logs.append(msg)
        return promoted, None, logs

    dropped = drop_fact(fact, verdict)
    msg = f"[CHECK-S3-DROP] {fact.subject!r}: {verdict.reason}"
    safe_print(msg)
    logs.append(msg)
    return None, dropped, logs


def fact_checker_node(state: "State", *, mode: str = "stub", dry_run: bool | None = None) -> dict:
    """
    inferred_facts 루프 → promoted_facts / dropped_hypotheses / fact_checker_log.

    ``mode``: ``live`` | ``corpus`` | ``stub`` (Sprint 5). Legacy ``dry_run`` overrides mode.
    """
    if dry_run is not None:
        mode = "stub" if dry_run else "live"

    _log("fact_checker_node enter")
    inferred = state.get("inferred_facts") or []
    fact_checker_log: list[str] = []

    if not inferred:
        _log("skip: no inferred_facts")
        fact_checker_log.append("[CHECK-S3-node] skip: no inferred facts")
        return {
            "promoted_facts": [],
            "dropped_hypotheses": [],
            "fact_checker_log": fact_checker_log,
        }

    corpus_pool = collect_corpus_pool(state) if mode == "corpus" else []
    _log(f"processing {len(inferred)} inferred fact(s) mode={mode} corpus_pool={len(corpus_pool)}")
    fact_checker_log.append(
        f"[CHECK-S3-node] batch size={len(inferred)} mode={mode} corpus_pool={len(corpus_pool)}"
    )

    promoted_facts: list[AtomicFact] = []
    dropped_hypotheses: list[DroppedHypothesis] = []

    for i, fact in enumerate(inferred, 1):
        _log(f"loop {i}/{len(inferred)}")
        with progress_sub(
            f"FC-{i}",
            f"팩트체크 {i}/{len(inferred)}",
            fact.subject[:40],
        ):
            promoted, dropped, step_logs = _check_one_hypothesis(
                fact,
                mode=mode,
                corpus_pool=corpus_pool,
            )
        fact_checker_log.extend(step_logs)
        if promoted is not None:
            promoted_facts.append(promoted)
        if dropped is not None:
            dropped_hypotheses.append(dropped)

    _log(
        f"exit promoted={len(promoted_facts)} dropped={len(dropped_hypotheses)}"
    )
    fact_checker_log.append(
        f"[CHECK-S3-node] done promoted={len(promoted_facts)} "
        f"dropped={len(dropped_hypotheses)}"
    )

    return {
        "promoted_facts": promoted_facts,
        "dropped_hypotheses": dropped_hypotheses,
        "fact_checker_log": fact_checker_log,
        "inferred_facts": [],
    }
