"""
Step 2 — Dreamer dry-run stub (Micro-step S2-4-stub)
======================================================

Flash 18개 breadth → Pro 압축 3개 (FC drop 테스트용 금융 1개 포함).
"""

from __future__ import annotations

import logging

from deconstructor.agents.dreamer.schemas import (
    FLASH_HYPOTHESIS_MIN,
    DreamHypothesis,
    DreamHypothesisBroadList,
    DreamHypothesisList,
)
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


def _factory_a_headline(raw_text: str, primary: AtomicFact) -> bool:
    text_lower = raw_text.lower()
    return (
        "factory a" in text_lower
        or "a공장" in text_lower
        or "a공장" in raw_text
        or "A공장" in raw_text
        or "factory" in primary.subject.lower()
        or "공장" in primary.subject
    )


def _core_factory_hypotheses(primary: AtomicFact) -> list[DreamHypothesis]:
    return [
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


def _core_generic_hypotheses(primary: AtomicFact) -> list[DreamHypothesis]:
    return [
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


def _breadth_variants(primary: AtomicFact) -> list[DreamHypothesis]:
    """Flash 단계용 중복·변형 후보."""
    base = primary.subject
    templates = [
        ("{s} HVAC load", "cooling -> offline", 3),
        ("{s} conveyor belt", "motion -> stopped", 4),
        ("{s} compressed air", "pressure -> decaying", 6),
        ("{s} wastewater pump", "flow -> stalled", 7),
        ("{s} lighting bus", "output -> zero", 1),
        ("{s} UPS battery", "discharge -> active", 2),
        ("{s} reactor agitator", "rpm -> zero", 9),
        ("{s} instrument air", "pressure -> low", 5),
        ("{s} fire suppression panel", "alarm -> latched", 11),
        ("{s} nitrogen purge", "flow -> interrupted", 12),
        ("{s} heat exchanger", "delta_t -> rising", 14),
        ("{s} sector equity index", "price -> volatile", 45),
        ("{s} forklift charging", "status -> suspended", 8),
        ("{s} raw material silo", "feed -> interrupted", 15),
        ("{s} emissions stack", "flow -> reduced", 20),
    ]
    out: list[DreamHypothesis] = []
    for subject_tpl, change, lag in templates:
        out.append(
            DreamHypothesis(
                source_fact_id=primary.id,
                subject=subject_tpl.format(s=base),
                state_change=change,
                lag_minutes=lag,
                mechanism=(
                    f"Loss or change at {base!r} propagates mechanically to "
                    f"{subject_tpl.format(s=base)} via shared plant infrastructure."
                ),
            )
        )
    return out


def stub_flash_breadth(
    source_facts: list[AtomicFact],
    *,
    raw_text: str = "",
) -> DreamHypothesisBroadList:
    """Flash stub — 최소 15개 breadth 후보."""
    if not source_facts:
        _log("stub flash: no source facts")
        raise ValueError("stub_flash_breadth requires at least one source fact")

    primary = _pick_primary_source(source_facts)
    _log(f"stub flash: primary id={primary.id[:8]}.. subject={primary.subject!r}")

    if _factory_a_headline(raw_text, primary):
        core = _core_factory_hypotheses(primary)
    else:
        core = _core_generic_hypotheses(primary)

    variants = _breadth_variants(primary)
    merged: list[DreamHypothesis] = []
    seen: set[tuple[str, str]] = set()
    for hyp in core + variants:
        key = (hyp.subject.lower(), hyp.state_change.lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(hyp)

    while len(merged) < FLASH_HYPOTHESIS_MIN:
        i = len(merged) + 1
        merged.append(
            DreamHypothesis(
                source_fact_id=primary.id,
                subject=f"{primary.subject} auxiliary load {i}",
                state_change="status -> derated",
                lag_minutes=5 + i,
                mechanism="Shared outage couples auxiliary loads to primary failure mode.",
            )
        )

    hyps = merged[:18]
    _log(f"stub flash: returning {len(hyps)} breadth candidate(s)")
    return DreamHypothesisBroadList(hypotheses=hyps)


def stub_pro_compress(
    source_facts: list[AtomicFact],
    broad: DreamHypothesisBroadList,
    *,
    raw_text: str = "",
) -> DreamHypothesisList:
    """Pro stub — 중복·비물리 제거 후 핵심 3개 (금융 1 포함)."""
    primary = _pick_primary_source(source_facts)
    _log(f"stub pro: compressing {len(broad.hypotheses)} → ≤3")

    if _factory_a_headline(raw_text, primary):
        finalists = _core_factory_hypotheses(primary)
    else:
        finalists = _core_generic_hypotheses(primary)

    _log(f"stub pro: returning {len(finalists)} finalist(s)")
    return DreamHypothesisList(hypotheses=finalists)


def stub_dream_hypotheses(
    source_facts: list[AtomicFact],
    *,
    raw_text: str = "",
) -> DreamHypothesisList:
    """2단계 stub: flash breadth → pro compress."""
    broad = stub_flash_breadth(source_facts, raw_text=raw_text)
    return stub_pro_compress(source_facts, broad, raw_text=raw_text)
