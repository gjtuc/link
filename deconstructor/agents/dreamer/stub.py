"""
Step 2 — Dreamer dry-run stub (Micro-step S2-4-stub)
======================================================

API 비용 없이 고정 3가설 반환.
예: A공장 정전 → 생산라인 정지 / B공장 전압 강하 / (금융 가설 — Step3에서 drop 테스트용)
"""

from __future__ import annotations

import logging

from deconstructor.agents.dreamer.schemas import DreamHypothesis, DreamHypothesisList
from deconstructor.models import AtomicFact

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[DREAM-S2-4] {msg}"
    logger.info(line)
    print(line)


def _pick_primary_source(sources: list[AtomicFact]) -> AtomicFact:
    """원천 fact: grid/factory/power 키워드 우선, 없으면 첫 번째."""
    keywords = ("factory", "grid", "power", "plant", "공장", "정전")
    for fact in sources:
        blob = f"{fact.subject} {fact.state_change}".lower()
        if any(k in blob for k in keywords):
            return fact
    return sources[0]


def stub_dream_hypotheses(
    source_facts: list[AtomicFact],
    *,
    raw_text: str = "",
) -> DreamHypothesisList:
    """
    하드코딩 3가설 — dry-run / 테스트 전용.

    [원천] A공장 정전 계열 → 3 파급 효과.
    """
    if not source_facts:
        _log("stub: no source facts — caller should skip")
        raise ValueError("stub_dream_hypotheses requires at least one source fact")

    primary = _pick_primary_source(source_facts)
    _log(f"stub: primary source id={primary.id[:8]}.. subject={primary.subject!r}")

    text_lower = raw_text.lower()
    factory_a = (
        "factory a" in text_lower
        or "a공장" in text_lower
        or "a공장" in raw_text
        or "A공장" in raw_text
    )

    if factory_a or "factory" in primary.subject.lower() or "공장" in primary.subject:
        hyps = [
            DreamHypothesis(
                source_fact_id=primary.id,
                subject="factory A production line",
                state_change="operation -> halted",
                lag_minutes=5,
                mechanism=(
                    "Grid power loss removes electrical supply; motor controllers "
                    "interlock and production line stops within minutes."
                ),
            ),
            DreamHypothesis(
                source_fact_id=primary.id,
                subject="nearby factory B grid voltage",
                state_change="voltage -> sag",
                lag_minutes=10,
                mechanism=(
                    "Sudden load rejection on shared feeder causes transient "
                    "voltage depression at adjacent factory B busbars."
                ),
            ),
            DreamHypothesis(
                source_fact_id=primary.id,
                subject="related sector equity index",
                state_change="price -> decline 10 percent",
                lag_minutes=60,
                mechanism=(
                    "Market participants reprice industrial outage exposure; "
                    "index futures sell pressure (fact-checker should drop non-physical)."
                ),
            ),
        ]
    else:
        hyps = [
            DreamHypothesis(
                source_fact_id=primary.id,
                subject=f"{primary.subject} downstream load",
                state_change="power draw -> zero",
                lag_minutes=2,
                mechanism="Upstream state change removes energy delivery to dependent load.",
            ),
            DreamHypothesis(
                source_fact_id=primary.id,
                subject=f"{primary.subject} backup supply",
                state_change="transfer switch -> activated",
                lag_minutes=5,
                mechanism="Automatic transfer switches engage when primary feed fails.",
            ),
            DreamHypothesis(
                source_fact_id=primary.id,
                subject=f"{primary.subject} cooling system",
                state_change="flow -> reduced",
                lag_minutes=8,
                mechanism="Loss of motive power reduces coolant circulation rate.",
            ),
        ]

    _log(f"stub: returning {len(hyps)} hardcoded hypotheses")
    return DreamHypothesisList(hypotheses=hyps)
