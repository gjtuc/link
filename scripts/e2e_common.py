"""Shared helpers for STAGE-0 manual E2E — Phase R then Phase A."""

from __future__ import annotations

import json
from typing import Any

from deconstructor.print_util import safe_print
from deconstructor.web.ingest_verify import ReadVerifyReport, verify_read
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.pipeline_batch import run_pipeline_batch


def run_read_phase(
    sources: list,
    *,
    scenario: str,
    raw_by_file: dict[str, str] | None = None,
) -> ReadVerifyReport:
    """Phase R — 읽기 확인 (LLM 0)."""
    report = verify_read(sources, raw_by_file=raw_by_file)
    safe_print(
        f"[{scenario}] Phase-R read_verify ok={report.ok} "
        f"passed={report.to_dict()['passed']}/{report.to_dict()['total']}"
    )
    failed = [c for c in report.checks if c.severity == "must" and not c.ok]
    if failed:
        safe_print(
            "[{0}] Phase-R MUST fail: ".format(scenario)
            + json.dumps([{"id": c.id, "detail": c.detail} for c in failed], ensure_ascii=False)
        )
    return report


def run_batch(
    sources: list,
    *,
    scenario: str = "E2E",
    raw_by_file: dict[str, str] | None = None,
    read_only: bool = False,
) -> tuple[dict[str, Any] | None, LinkStepTracker | None, ReadVerifyReport]:
    """
    Phase R then optional Phase A.

    Returns (pipeline_result, tracker, read_report).
    If read fails or read_only, pipeline_result is None.
    """
    read_report = run_read_phase(sources, scenario=scenario, raw_by_file=raw_by_file)
    if not read_report.ok:
        return None, None, read_report
    if read_only:
        return None, None, read_report
    tracker = LinkStepTracker()
    result = run_pipeline_batch(sources, tracker=tracker)
    return result, tracker, read_report


def print_checklist(scenario: str, checklist: dict[str, Any]) -> None:
    safe_print(f"[{scenario}] checklist: " + json.dumps(checklist, ensure_ascii=False, indent=2))


def fail_or_pass(
    scenario: str,
    result: dict[str, Any],
    checklist: dict[str, Any],
    *,
    pass_detail: str,
) -> int:
    print_checklist(scenario, checklist)
    if not result.get("ok"):
        safe_print(f"[{scenario}] FAIL: {result.get('message')} {result.get('failed_step')}")
        return 2
    safe_print(f"[{scenario}] PASS - {pass_detail}")
    return 0
