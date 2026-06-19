"""

LangGraph node wrapper for The Skeptic.

The Skeptic용 LangGraph 노드 래퍼.



Purpose / 목적

--------------

Bridge the deconstructor pipeline ``State`` to ``SkepticEngine``: run causal

verification on ``completed_facts``, optionally retry INCONCLUSIVE pairs, and

write results back into graph state fields.

파이프라인 ``State``와 ``SkepticEngine``을 연결한다. ``completed_facts``에 대해

인과 검증을 실행하고, INCONCLUSIVE 쌍을 재시도한 뒤 그래프 state 필드에 결과를 기록한다.



Pipeline position / 파이프라인 위치

---------------------------------

  … → decomposition / fact completion  →  **skeptic_node**  →  downstream graph build



This is the only entry point that combines engine + retry + partial-run logging

for production LangGraph runs.

엔진 + 재시도 + 부분 실행 로깅을 결합하는 프로덕션 LangGraph 진입점이다.



When to modify / 수정 시점

--------------------------

- New state keys for skeptic output: update return dict and pipeline ``State`` type.

- Retry policy changes: edit ``retry/orchestrate.py``, not rule logic here.

- ``dry_run=False`` for live LLM mechanism fill — ensure env/LLM config upstream.

- 스케ptic 출력용 state 키 추가 시 반환 dict와 ``State`` 타입을 함께 수정.

- 재시도 정책은 ``retry/orchestrate.py``에서 변경.



Key invariants / 핵심 불변조건

------------------------------

- Fewer than 2 facts → skip batch, empty edges, ``ran_batch=False`` in log.

- ``partial_run`` flags are always set from ``detect_partial_run`` — skeptic does

  not override decomposition truncation signals.

- ``skeptic_verdicts`` preserves full per-pair traces for reporting/debug.

- 사실 2개 미만이면 배치 생략, 빈 엣지, 로그 ``ran_batch=False``.

- ``partial_run``은 ``detect_partial_run`` 결과를 그대로 반영한다.

"""



from __future__ import annotations



from typing import TYPE_CHECKING



from deconstructor.pipeline.partial_run import detect_partial_run

from deconstructor.skeptic.engine import SkepticEngine

from deconstructor.skeptic.retry import retry_inconclusive

from deconstructor.skeptic.run_log import SkepticLogEntry, build_skeptic_log

from deconstructor.web.progress_ctx import progress_sub


if TYPE_CHECKING:

    from deconstructor.pipeline.state import State


def skeptic_node(state: "State", *, dry_run: bool = True) -> dict:

    """

    Run codified causal verification on ``completed_facts``.

    ``completed_facts``에 대해 코딩된 인과 검증을 실행한다.



    Sets ``partial_run`` and ``skeptic_log``. Retries INCONCLUSIVE pairs

    with mechanism fill (stub when ``dry_run=True``).

    ``partial_run``·``skeptic_log``를 설정하고, INCONCLUSIVE 쌍은 메커니즘 보강 후

    재평가한다(``dry_run=True``이면 스텁 사용).



    Args:

        state: LangGraph pipeline state with ``completed_facts``, recursion caps.

        dry_run: If True, mechanism retry uses ``stub_mechanism`` not live LLM.



    Returns:

        Partial state update dict (edges, rejections, verdicts, log, partial flags).



    수정 시 주의점:

        Default ``dry_run=True`` keeps CI/local runs deterministic — flip only when

        LLM credentials and structured output are configured.

        Early return path must still set ``partial_run`` for downstream consumers.

    """

    partial = detect_partial_run(

        extracted_facts=state["extracted_facts"],

        completed_facts=state["completed_facts"],

        recursion_depth=state["recursion_depth"],

        max_recursion_depth=state["max_recursion_depth"],

    )



    facts = list(state["completed_facts"]) + list(state.get("promoted_facts") or [])
    print(
        f"[STEP4-skeptic] evaluating {len(facts)} facts "
        f"(completed={len(state['completed_facts'])}, "
        f"promoted={len(state.get('promoted_facts') or [])})"
    )

    if len(facts) < 2:

        # Cannot form any directed pair — skip engine entirely.

        log = build_skeptic_log(

            partial, completed_fact_count=len(facts), ran_batch=False

        )

        return {

            "partial_run": partial.partial_run,

            "partial_run_reason": partial.reason,

            "skeptic_log": log,

            "verified_edges": [],

            "rejected_hypotheses": [],

            "skeptic_verdicts": [],

        }



    engine = SkepticEngine()

    pair_count = len(facts) * (len(facts) - 1)
    with progress_sub(
        "SKEPTIC-BATCH",
        "인과 쌍 규칙 검증",
        f"facts={len(facts)} pairs≈{pair_count}",
    ):
        batch = engine.evaluate_batch(facts)

    with progress_sub("SKEPTIC-RETRY", "INCONCLUSIVE 재검증"):
        batch, retry_log = retry_inconclusive(
            engine, facts, batch, dry_run=dry_run
        )



    log = build_skeptic_log(

        partial, completed_fact_count=len(facts), ran_batch=True

    )

    log.extend(retry_log)



    return {

        "partial_run": partial.partial_run,

        "partial_run_reason": partial.reason,

        "skeptic_log": log,

        "verified_edges": batch.verified_edges,

        "rejected_hypotheses": batch.rejected,

        "skeptic_verdicts": batch.verdicts,

    }


