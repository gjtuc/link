#!/usr/bin/env python3
"""
μ-REG-B1-smoke — Branch-1 short regression (pipeline_batch ingest touch).

μ-ID: μ-REG-B1-smoke (L1 live)
선행: μ-REG-S0 — stage0_reaudit_baseline + phase_r exit 0
실행: python scripts/branch1_regression_smoke.py [--skip-phase-r]
스펙: docs/design/BRANCH-1-spec.md § REG-B1-smoke

S0-B short 1청크만 Phase A (run_pipeline_batch 경로). full branch1_full_e2e(~542s) 대신.
LINK_DISABLE_NEO4J_AUTO_START **미설정** — 기본 R→A·S5 계약 확인.
산출: logs/branch1_regression/YYYYMMDD-HHMM-smoke.json
"""

from __future__ import annotations

import argparse
import json
import os
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

SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
LOG_DIR = ROOT / "logs" / "branch1_regression"


def ensure_phase_r(*, skip: bool = False) -> int:
    if skip:
        return 0
    return subprocess.call([sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT)


def _s5_steps(steps: list[dict] | None) -> list[dict]:
    if not steps:
        return []
    return [s for s in steps if s.get("step", "").startswith("S5-")]


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser(description="μ-REG-B1-smoke — S0-B short batch regression")
    ap.add_argument("--skip-phase-r", action="store_true", help="phase_r already run (μ-REG-S0)")
    args = ap.parse_args()

    os.environ.pop("LINK_DISABLE_NEO4J_AUTO_START", None)

    t0 = time.monotonic()
    pr = ensure_phase_r(skip=args.skip_phase_r)
    if pr != 0:
        safe_print(f"[REG-B1-smoke] ABORT phase_r exit {pr}")
        return pr

    if not SHORT.is_file():
        safe_print(f"[REG-B1-smoke] Missing {SHORT}")
        return 1

    text = SHORT.read_text(encoding="utf-8")
    sources = expand_document_sources("short", from_text(text), kind="text", source_file=SHORT.name)
    result, tracker, read_report = run_batch(
        sources,
        scenario="REG-B1-smoke",
        raw_by_file={SHORT.name: text},
        read_only=False,
    )
    elapsed = round(time.monotonic() - t0, 1)

    steps = (tracker.to_list() if tracker else []) or (result or {}).get("steps") or []
    s5 = _s5_steps(steps)
    pipeline_ok = bool(result and result.get("ok"))
    sk = (result or {}).get("skeleton") or {}
    fc = (result or {}).get("fact_checker") or {}

    checklist = {
        "Phase-R_ok": read_report.ok,
        "pipeline_ok": pipeline_ok,
        "atomic_facts_total": (result or {}).get("atomic_facts_total"),
        "gap_count": sk.get("gap_count"),
        "weak_count": sk.get("weak_count"),
        "fc_mode": fc.get("mode"),
        "neo4j_persisted": (result or {}).get("neo4j_persisted"),
        "s5_step_count": len(s5),
        "s5_steps": [s.get("step") for s in s5],
        "link_disable_neo4j_auto_start": os.getenv("LINK_DISABLE_NEO4J_AUTO_START"),
        "failed_step": None if pipeline_ok else (result or {}).get("failed_step"),
        "elapsed_sec": elapsed,
    }
    print_checklist("REG-B1-smoke", checklist)

    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "scenario": "REG-B1-smoke",
        "mu_id": "μ-REG-B1-smoke",
        "phase_r_exit": pr,
        "exit_code": 0 if pipeline_ok else 2,
        "checklist": checklist,
        "s5_detail": s5,
        "baseline_commit": "7937b59",
        "note": "post μ-PROBE-S5 pipeline_batch touch; not full REG-B1b",
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = LOG_DIR / f"{stamp}-smoke.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(f"[REG-B1-smoke] wrote {out_path}")

    if not pipeline_ok:
        safe_print(f"[REG-B1-smoke] FAIL: {(result or {}).get('failed_step')}")
        return 2

    safe_print(f"[REG-B1-smoke] PASS elapsed={elapsed}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
