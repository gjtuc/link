"""
Structured skeptic logging for partial and skipped runs.
부분 실행·생략 실행용 구조화 스케ptic 로그.

Purpose / 목적
--------------
Emit machine-readable ``SkepticLogEntry`` lines for pipeline observability:
partial decomposition, depth cap, insufficient facts, batch completion.
파이프라인 관측용 ``SkepticLogEntry``를 생성한다 — 부분 분해, 깊이 상한,
사실 부족, 배치 완료 등.

Pipeline position / 파이프라인 위치
---------------------------------
  skeptic_node  →  **build_skeptic_log**  (+ retry log entries appended after)

When to modify / 수정 시점
--------------------------
- New log codes: document in pipeline consumers; keep ``level`` INFO|WARN|SKIP.
- Depth-cap warning tied to ``REASON_DEPTH_CAP`` from partial_run module.
- 새 log code 추가 시 downstream 소비자와 합의.

Key invariants / 핵심 불변조건
------------------------------
- L3 path returns early — no BATCH_COMPLETE when <2 facts.
- ``ran_batch=False`` when skeptic engine never invoked.
- 사실 2개 미만이면 BATCH_COMPLETE 없이 조기 반환.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from deconstructor.pipeline.partial_run import PartialRunInfo, REASON_DEPTH_CAP


class SkepticLogEntry(BaseModel):
    """
    One line in the skeptic execution log.
    스케ptic 실행 로그 한 줄.

    ``code``: stable identifier for filtering (e.g. SKEPTIC_START, RETRY_DONE).
    """

    level: str = Field(description="INFO | WARN | SKIP")
    code: str
    message: str


def build_skeptic_log(
    partial: PartialRunInfo,
    *,
    completed_fact_count: int,
    ran_batch: bool,
) -> list[SkepticLogEntry]:
    """
    Build explicit log entries for partial / complete skeptic passes.
    부분·완전 스케ptic 패스에 대한 명시적 로그 항목 생성.

    Micro-steps:
      L1 - record partial_run flag
      L2 - warn on incomplete input
      L3 - skip when <2 facts
      L4 - note batch execution

    Args:
        partial: Decomposition completeness info from ``detect_partial_run``.
        completed_fact_count: len(completed_facts) at skeptic entry.
        ran_batch: True if ``SkepticEngine.evaluate_batch`` actually ran.

    Returns:
        Ordered list of log entries (retry entries added separately in node).

    수정 시 주의점:
        Do not log fact contents — counts and flags only for privacy/size.
    """
    entries: list[SkepticLogEntry] = []

    # L1: always log skeptic invocation context.
    entries.append(
        SkepticLogEntry(
            level="INFO",
            code="SKEPTIC_START",
            message=(
                f"partial_run={partial.partial_run} "
                f"completed_atomic={completed_fact_count}"
            ),
        )
    )

    if partial.partial_run:
        entries.append(
            SkepticLogEntry(
                level="WARN",
                code="PARTIAL_INPUT",
                message=(
                    f"incomplete decomposition: reason={partial.reason} "
                    f"non_atomic={partial.non_atomic_count} "
                    f"depth={partial.recursion_depth}/{partial.max_recursion_depth}"
                ),
            )
        )
        # Extra warning when depth cap truncated before null floor — graph unreliable.
        if partial.reason == REASON_DEPTH_CAP:
            entries.append(
                SkepticLogEntry(
                    level="WARN",
                    code="DEPTH_CAP_TRUNCATION",
                    message="depth cap hit before null floor - causal graph unreliable",
                )
            )

    if completed_fact_count < 2:
        entries.append(
            SkepticLogEntry(
                level="SKIP",
                code="INSUFFICIENT_FACTS",
                message="fewer than 2 completed atomic facts - skeptic batch skipped",
            )
        )
        return entries

    if ran_batch:
        entries.append(
            SkepticLogEntry(
                level="INFO",
                code="BATCH_COMPLETE",
                message="pairwise causal verification executed",
            )
        )

    return entries
