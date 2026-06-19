"""
Step 2 — Dreamer LangGraph 노드 (Micro-step S2-6)
==================================================

Purpose / 목적
--------------
``completed_facts``(파랑·검증된 원자 사실)에서 **가로 방향 파급 가설**을 생성한다.
출력은 Fact-Checker → Skeptic 으로 이어지는 ``inferred_facts`` (노랑·pending).

2단계 LLM (2026-06 절충안)
---------------------------
  ① Flash 1회 — 15~20개 breadth (넓게, 중복·약한 후보 허용)
  ② Pro 1회 — 원문 fact anchor, 중복·비물리 제거, **≤5** + mechanism
  ③ Fact-Checker — finalists만 Tavily+Verifier (또는 stub)
  ④ Skeptic — 기존과 동일 (n×(n−1) 규칙 검사)

Pipeline position
-----------------
  verify → **dreamer** → fact_checker → skeptic → weaver

Dry-run
-------
  ``stub_flash_breadth`` → ``stub_pro_compress`` (동일 2단계, 고정 후보).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.llm_runner import invoke_dream_hypotheses
from deconstructor.agents.dreamer.schemas import PRO_HYPOTHESIS_MAX

if TYPE_CHECKING:
    from deconstructor.pipeline.state import State

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-6] {msg}"
    logger.info(line)
    print(line)


def dreamer_node(state: "State", *, dry_run: bool = False) -> dict:
    """
    completed_facts → inferred_facts (source_type=inferred, check_status=pending).

    Live: Flash(tier=flash) breadth → Pro(tier=pro) compress (≤5).
    Stub: 동일 2단계 흐름, 고정 후보.
    """
    _log("dreamer_node enter")
    source_facts = state["completed_facts"]
    headline = state["raw_text"]
    dreamer_log: list[str] = []

    if not source_facts:
        _log("skip: no completed_facts — inferred_facts=[]")
        dreamer_log.append("[DREAM-S2-6] skip: no source facts")
        return {"inferred_facts": [], "dreamer_log": dreamer_log}

    _log(f"source_facts count={len(source_facts)} dry_run={dry_run}")
    dreamer_log.append(f"[DREAM-S2-6] sources={len(source_facts)} dry_run={dry_run}")

    if dry_run:
        _log("routing to stub 2-stage (flash→pro)")
        from deconstructor.agents.dreamer.stub import stub_flash_breadth, stub_pro_compress

        broad = stub_flash_breadth(source_facts, raw_text=headline)
        dreamer_log.append(
            f"[DREAM-S2-6] flash breadth={len(broad.hypotheses)}"
        )
        result = stub_pro_compress(source_facts, broad, raw_text=headline)
    else:
        _log("routing to live 2-stage (flash→pro)")
        result = invoke_dream_hypotheses(source_facts, headline=headline)

    dreamer_log.append(
        f"[DREAM-S2-6] pro finalists={len(result.hypotheses)} "
        f"(max {PRO_HYPOTHESIS_MAX} for fact_checker)"
    )
    inferred = apply_hypotheses(result, source_facts)
    dreamer_log.append(f"[DREAM-S2-6] inferred_facts={len(inferred)}")

    _log(f"dreamer_node exit inferred={len(inferred)}")
    return {
        "inferred_facts": inferred,
        "dreamer_log": dreamer_log,
    }
