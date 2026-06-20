"""Shared helpers for STAGE-0 manual E2E scripts (S0-A/B/C)."""

from __future__ import annotations

import json
from typing import Any

from deconstructor.print_util import safe_print
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.pipeline_batch import run_pipeline_batch


def run_batch(sources: list) -> tuple[dict[str, Any], LinkStepTracker]:
    tracker = LinkStepTracker()
    result = run_pipeline_batch(sources, tracker=tracker)
    return result, tracker


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
