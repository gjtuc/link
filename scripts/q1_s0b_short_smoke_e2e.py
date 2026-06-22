#!/usr/bin/env python3
"""
μ-Q1-E2E — S0-B short live smoke (2-pass pipeline, 1 source).

  python scripts/q1_s0b_short_smoke_e2e.py

Prerequisite: phase_r_regression exit 0 (invoked at start).
Output: logs/q1_e2e_smoke/s0b-short-YYYYMMDD-HHMM.json
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor import config
from deconstructor.agents.dreamer.pass2_inputs import select_pass2_source_facts
from deconstructor.print_util import bootstrap_stdio_utf8, safe_print
from deconstructor.skeleton import skeleton_index
from deconstructor.viz.state_graph import graph_from_pipeline_state
from deconstructor.web.extract import expand_document_sources, from_text
from deconstructor.web.ingest_verify import verify_read
from deconstructor.web.link_steps import LinkStepTracker
from deconstructor.web.pipeline_link import run_pipeline_with_steps

SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
LOG_DIR = ROOT / "logs" / "q1_e2e_smoke"
V5_BASELINE_PASS2_SOURCE_COUNT = 5  # s0b V5 pass2 probe (8265da4)

REQUIRED_CHECKLIST_KEYS = frozenset(
    {
        "Phase-R_ok",
        "pipeline_ok",
        "pass1_edge_count",
        "pass2_gap_count",
        "pass2_source_count",
        "promoted_count",
        "gap_count",
        "weak_count",
        "fc_mode",
    }
)


def _parse_dreamer_counts(dreamer_log: list[str]) -> tuple[int | None, int | None]:
    src, gap = None, None
    for line in dreamer_log or []:
        if "pass2_source_count=" not in line:
            continue
        for part in line.split():
            if part.startswith("pass2_source_count="):
                src = int(part.split("=", 1)[1])
            elif part.startswith("pass2_gap_count="):
                gap = int(part.split("=", 1)[1])
    return src, gap


def build_q1_checklist(
    *,
    read_ok: bool,
    state: dict,
    skeleton: dict,
    fc_mode: str,
    elapsed_sec: float,
) -> dict:
    pass1_edges = state.get("verified_edges_pass1") or []
    gap_nodes = state.get("pass2_gap_nodes") or []
    pass2_sources = select_pass2_source_facts(
        state.get("completed_facts") or [],
        pass1_edges,
        gap_nodes=gap_nodes,
    )
    log_src, log_gap = _parse_dreamer_counts(state.get("dreamer_log") or [])
    if pass2_sources:
        pass2_source_count = len(pass2_sources)
    elif log_src is not None:
        pass2_source_count = log_src
    else:
        pass2_source_count = 0
    pass2_gap_count = len(gap_nodes) if gap_nodes else (log_gap if log_gap is not None else 0)
    promoted = state.get("promoted_facts") or []
    dropped = state.get("dropped_hypotheses") or []
    verified_2 = state.get("verified_edges") or []

    checklist = {
        "Phase-R_ok": read_ok,
        "pipeline_ok": read_ok
        and len(state.get("completed_facts") or []) > 0
        and skeleton.get("gap_count") is not None,
        "pass1_edge_count": len(pass1_edges),
        "pass2_gap_count": pass2_gap_count,
        "pass2_source_count": pass2_source_count,
        "pass2_source_count_from_log": log_src,
        "pass2_gap_count_from_log": log_gap,
        "promoted_count": len(promoted),
        "dropped_count": len(dropped),
        "verified_edges_pass2_count": len(verified_2),
        "gap_count": skeleton.get("gap_count"),
        "weak_count": skeleton.get("weak_count"),
        "fc_mode": fc_mode,
        "partial_run": state.get("partial_run"),
        "elapsed_sec": round(elapsed_sec, 1),
        "v5_baseline_pass2_source_count": V5_BASELINE_PASS2_SOURCE_COUNT,
        "v5_vs_smoke_pass2_source_match": pass2_source_count == V5_BASELINE_PASS2_SOURCE_COUNT,
        "v5_note": "V5 probe deconstruct=5; smoke deconstruct may differ",
        "deconstruct_fact_count": len(state.get("completed_facts") or []),
        "pass2_source_ids": [f.id for f in pass2_sources],
    }
    return checklist


def _write_log(payload: dict, stamp: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"s0b-short-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    bootstrap_stdio_utf8()
    t0 = time.monotonic()

    safe_print("[Q1-E2E] phase_r_regression (prerequisite)")
    pr_rc = subprocess.call([sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT)
    if pr_rc != 0:
        safe_print(f"[Q1-E2E] ABORT: phase_r_regression exit {pr_rc}")
        return pr_rc

    if not SHORT.is_file():
        safe_print("[Q1-E2E] missing fixture — generate_s0bc_fixtures.py")
        return 1

    short_text = SHORT.read_text(encoding="utf-8")
    sources = expand_document_sources(
        "short",
        from_text(short_text),
        kind="text",
        source_file=SHORT.name,
    )
    read_report = verify_read(sources, raw_by_file={SHORT.name: short_text})
    if not read_report.ok:
        safe_print("[Q1-E2E] FAIL Phase-R")
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        _write_log(
            {
                "scenario": "S0-B-short-Q1-smoke",
                "exit_code": 2,
                "checklist": {"Phase-R_ok": False, "read_verify": read_report.to_dict()},
            },
            stamp,
        )
        return 2

    fc_mode = config.resolve_fact_checker_mode()
    tracker = LinkStepTracker()
    safe_print(f"[Q1-E2E] live pipeline short only fc_mode={fc_mode}")

    try:
        state = run_pipeline_with_steps(
            tracker,
            1,
            short_text,
            enable_dreamer=True,
            fact_checker_mode=fc_mode,
            fact_checker_dry_run=(fc_mode == "stub"),
            source_document_meta=sources[0].document_meta_dict() if sources else {},
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        dreamer_tail = []
        _write_log(
            {
                "scenario": "S0-B-short-Q1-smoke",
                "exit_code": 3,
                "error": str(exc),
                "elapsed_sec": round(elapsed, 1),
                "dreamer_log_tail": dreamer_tail,
                "steps_tail": tracker.to_list()[-10:],
            },
            stamp,
        )
        safe_print(f"[Q1-E2E] FAIL pipeline: {exc}")
        return 3

    fetched = graph_from_pipeline_state(state)
    skeleton = skeleton_index(list(fetched.nodes), list(fetched.edges))
    elapsed = time.monotonic() - t0
    checklist = build_q1_checklist(
        read_ok=True,
        state=state,
        skeleton=skeleton,
        fc_mode=fc_mode,
        elapsed_sec=elapsed,
    )

    dreamer_log = state.get("dreamer_log") or []
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    exit_code = 0 if checklist.get("pipeline_ok") else 4
    payload = {
        "scenario": "S0-B-short-Q1-smoke",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "exit_code": exit_code,
        "checklist": checklist,
        "dreamer_log_tail": dreamer_log[-10:],
        "steps_count": len(tracker.to_list()),
    }
    log_path = _write_log(payload, stamp)
    safe_print("[Q1-E2E] checklist: " + json.dumps(checklist, ensure_ascii=False, indent=2))
    safe_print(f"[Q1-E2E] wrote {log_path}")

    if exit_code == 0:
        safe_print(
            f"[Q1-E2E] PASS elapsed={checklist['elapsed_sec']}s "
            f"pass1={checklist['pass1_edge_count']} pass2_src={checklist['pass2_source_count']} "
            f"gap={checklist['gap_count']} weak={checklist['weak_count']}"
        )
    else:
        safe_print(f"[Q1-E2E] FAIL pipeline_ok=false elapsed={checklist['elapsed_sec']}s")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
