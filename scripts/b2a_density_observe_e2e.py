#!/usr/bin/env python3
"""
μ-B2a-01 — AC-DEC-02 median completed_facts observe E2E.

μ-ID: μ-B2a-01
선행: branch_2_unlocked=true, phase_r_regression exit 0
실행: python scripts/b2a_density_observe_e2e.py [--skip-phase-r]
스펙: docs/design/BRANCH-2a-spec.md · AC-DEC-02 (SHOULD median≥5, 관측만)

입력: S0-B fixtures (short 1청크 + long 3청크 = 4 runs).
산출: logs/b2a_density/*-detail.json, logs/capability_runs/*-b2a-density-observe.json
합격: Phase R ok + pipeline ok (median 미달은 exit 0, detail에 관측 기록).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import bootstrap_stdio_utf8, safe_print
from deconstructor.web.extract import expand_document_sources, from_text
from scripts.e2e_common import print_checklist, run_batch
from scripts.log_capability_run import log_capability_run

SCRIPT_NAME = "b2a_density_observe_e2e.py"
CAP_ID = "b2a-density-observe"
DETAIL_DIR = ROOT / "logs" / "b2a_density"
STATE = ROOT / "tests" / "fixtures" / "branch_state.json"
SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
LONG = ROOT / "tests" / "fixtures" / "s0b_draft_long.txt"
AC_DEC_02_MEDIAN_TARGET = 5


def ensure_phase_r(*, skip: bool = False) -> int:
    if skip:
        return 0
    return subprocess.call([sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT)


def _assert_branch_unlocked() -> int | None:
    if not STATE.is_file():
        safe_print("[B2a] WARN: branch_state.json missing")
        return None
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if not state.get("branch_2_unlocked"):
        safe_print("[B2a] ABORT: branch_2_unlocked=false (run unlock_branch2.py post-probe)")
        return 4
    if not state.get("branch_1_complete"):
        safe_print("[B2a] ABORT: branch_1_complete=false")
        return 4
    return None


def _write_detail(detail: dict) -> Path:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    path = DETAIL_DIR / f"{stamp}-b2a-density-detail.json"
    path.write_text(json.dumps(detail, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _finish(exit_code: int, detail: dict) -> int:
    detail_path = _write_detail(detail)
    run_path = log_capability_run(CAP_ID, SCRIPT_NAME, exit_code)
    safe_print(f"[B2a] detail {detail_path}")
    safe_print(f"[B2a] run log {run_path}")
    safe_print(f"[B2a] exit={exit_code}")
    return exit_code


def _load_s0b_sources():
    if not SHORT.is_file() or not LONG.is_file():
        raise FileNotFoundError("Missing S0-B fixtures — run generate_s0bc_fixtures.py")
    short_text = SHORT.read_text(encoding="utf-8")
    long_text = LONG.read_text(encoding="utf-8")
    short_src = expand_document_sources("short", from_text(short_text), kind="text", source_file=SHORT.name)
    long_src = expand_document_sources("long", from_text(long_text), kind="text", source_file=LONG.name)
    sources = short_src + long_src
    raw_map = {SHORT.name: short_text, LONG.name: long_text}
    return sources, raw_map


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser(description="μ-B2a-01 AC-DEC-02 density observe E2E")
    ap.add_argument("--skip-phase-r", action="store_true", help="phase_r already run")
    args = ap.parse_args()

    lock_rc = _assert_branch_unlocked()
    if lock_rc is not None:
        return lock_rc

    t0 = time.monotonic()
    pr = ensure_phase_r(skip=args.skip_phase_r)
    if pr != 0:
        detail = {
            "mu_id": "μ-B2a-01",
            "scenario": "B2a-DENSITY",
            "fixture": "s0b_draft_short+long",
            "phase_r_exit": pr,
            "pipeline_ok": False,
            "failed_step": "phase_r_regression",
            "elapsed_sec": round(time.monotonic() - t0, 1),
        }
        return _finish(1, detail)

    try:
        sources, raw_map = _load_s0b_sources()
    except FileNotFoundError as exc:
        safe_print(f"[B2a] {exc}")
        return 1

    result, _, read_report = run_batch(
        sources,
        scenario="B2a-DENSITY",
        raw_by_file=raw_map,
        read_only=False,
    )
    elapsed = round(time.monotonic() - t0, 1)

    if not read_report.ok:
        detail = {
            "mu_id": "μ-B2a-01",
            "scenario": "B2a-DENSITY",
            "fixture": "s0b_draft_short+long",
            "phase_r_ok": False,
            "pipeline_ok": False,
            "failed_step": "read_verify",
            "elapsed_sec": elapsed,
        }
        return _finish(2, detail)

    pipeline_ok = bool(result and result.get("ok"))
    debug = (result or {}).get("pipeline_debug") or {}
    batch = debug.get("deconstruct_batch") or {}
    median = float(batch.get("median_completed_facts") or 0)
    per_run = list(batch.get("completed_facts_per_run") or [])
    runs_meta = [
        {
            "chunk_id": (r.get("source_document_meta") or {}).get("chunk_id", ""),
            "completed_facts": r.get("counts", {}).get("completed_facts", 0),
            "recursion_depth": r.get("deconstruct", {}).get("recursion_depth", 0),
        }
        for r in debug.get("pipeline_runs") or []
    ]

    meets_should = median >= AC_DEC_02_MEDIAN_TARGET
    checklist = {
        "Phase-R_ok": True,
        "pipeline_ok": pipeline_ok,
        "runs": len(per_run),
        "completed_facts_per_run": per_run,
        "median_completed_facts": median,
        "ac_dec_02_median_target": AC_DEC_02_MEDIAN_TARGET,
        "ac_dec_02_meets_should": meets_should,
        "runs_with_depth_gt_1": batch.get("runs_with_depth_gt_1"),
        "atomic_facts_total": (result or {}).get("atomic_facts_total"),
        "failed_step": None if pipeline_ok else (result or {}).get("failed_step"),
        "elapsed_sec": elapsed,
    }
    print_checklist("B2a-DENSITY", checklist)

    detail = {
        "mu_id": "μ-B2a-01",
        "scenario": "B2a-DENSITY",
        "fixture": "s0b_draft_short+long",
        "files": [SHORT.name, LONG.name],
        "phase_r_ok": True,
        "pipeline_ok": pipeline_ok,
        "failed_step": None if pipeline_ok else (result or {}).get("failed_step"),
        "elapsed_sec": elapsed,
        "ac_dec_02_median_target": AC_DEC_02_MEDIAN_TARGET,
        "ac_dec_02_meets_should": meets_should,
        "deconstruct_batch": {
            "runs": batch.get("runs", len(per_run)),
            "completed_facts_per_run": per_run,
            "median_completed_facts": median,
            "runs_with_depth_gt_1": batch.get("runs_with_depth_gt_1"),
            "recursion_depths": batch.get("recursion_depths"),
            "partial_run_count": batch.get("partial_run_count"),
        },
        "per_run_meta": runs_meta,
    }

    if not pipeline_ok:
        safe_print("[B2a] FAIL Phase-A")
        return _finish(3, detail)

    note = "meets SHOULD" if meets_should else "below SHOULD (observation only)"
    safe_print(
        f"[B2a] PASS — median_completed_facts={median} "
        f"target={AC_DEC_02_MEDIAN_TARGET} ({note})"
    )
    return _finish(0, detail)


if __name__ == "__main__":
    raise SystemExit(main())
