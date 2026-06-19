"""

Human-readable skeptic batch report.

사람이 읽기 쉬운 스케ptic 배치 리포트.



Purpose / 목적

--------------

Format ``SkepticBatchResult`` as plain-text trace for CLI, tests, and debugging.

Recomputes aggregation trace per verdict for display (does not mutate batch).

``SkepticBatchResult``를 평문 추적으로 포맷 — CLI·테스트·디버깅용.

표시를 위해 가설별 집계 추적을 재계산(배치 데이터 변경 없음).



Pipeline position / 파이프라인 위치

---------------------------------

  Optional consumer after engine/node — not on critical pipeline path.

  엔진/노드 이후 선택적 소비자 — 핵심 파이프라인 경로 아님.



When to modify / 수정 시점

--------------------------

- Output format only — do not embed business logic here.

- Id truncation ([:8]) is cosmetic for terminal width.

- 출력 형식만 변경 — 비즈니스 로직 금지.



Key invariants / 핵심 불변조건

------------------------------

- ``format_hypothesis_verdict`` must stay consistent with ``aggregate_verdict``.

- Report includes every verdict in batch, not only verified/rejected summaries.

"""



from __future__ import annotations



from deconstructor.skeptic.aggregator import aggregate_verdict

from deconstructor.skeptic.schemas import HypothesisVerdict, SkepticBatchResult





def format_hypothesis_verdict(v: HypothesisVerdict) -> list[str]:

    """

    Render one hypothesis verdict as indented text lines.

    단일 가설 판정을 들여쓰기 텍스트 줄 목록으로 렌더.



    Args:

        v: Aggregated verdict with full rule_results trace.



    Returns:

        List of strings (no trailing newlines per line).



    수정 시 주의점:

        Re-runs ``aggregate_verdict`` for agg trace — must match stored ``accepted``.

    """

    lines = [

        f"  {v.hypothesis.source_fact_id[:8]}.. -> "

        f"{v.hypothesis.target_fact_id[:8]}.. "

        f"[{v.final_classification.value}] accepted={v.accepted}"

    ]

    for r in v.rule_results:

        mark = r.outcome.value[0].upper()  # P/F/A first letter

        lines.append(f"    [{mark}] {r.rule_id}: {r.reason}")

    _, _, agg_trace = aggregate_verdict(v.rule_results)

    if agg_trace:

        steps = " -> ".join(s.step_id for s in agg_trace)

        lines.append(f"    agg: {steps} => {agg_trace[-1].outcome}")

    return lines





def format_skeptic_report(batch: SkepticBatchResult) -> str:

    """

    Build full multi-hypothesis skeptic report string.

    전체 다중 가설 스케ptic 리포트 문자열 생성.



    Args:

        batch: Complete batch result from engine (possibly merged after retry).



    Returns:

        Single string with separator lines and per-verdict blocks.



    수정 시 주의점:

        Verdict order follows ``batch.verdicts`` list order from engine.

    """

    sep = "=" * 60

    lines = [

        sep,

        "  SKEPTIC REPORT - rule-by-rule trace",

        sep,

        f"verified: {len(batch.verified_edges)}  rejected: {len(batch.rejected)}",

        "",

    ]

    for v in batch.verdicts:

        lines.extend(format_hypothesis_verdict(v))

        lines.append("")

    lines.append(sep)

    return "\n".join(lines)


