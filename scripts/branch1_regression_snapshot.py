#!/usr/bin/env python3
"""
μ-REG-B1b/c — Branch-1 regression snapshot (post-Q1).

μ-ID: μ-REG-B1b (branch1_full_e2e), μ-REG-B1c (관측 JSON)
선행: μ-REG-B1a phase_r_regression exit 0
실행: python scripts/branch1_regression_snapshot.py
스펙: docs/design/BRANCH-1-spec.md § REG-B1 — Q1 후 회귀

Baseline (비교용, 실패 조건 아님): gap=20, weak=3 (S0-B); bridge=1 (S0-C).
Fixture 샘플: tests/fixtures/branch1_regression_sample.json
Live 로그: logs/branch1_regression/YYYYMMDD-HHMM-regression.json (gitignore)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import bootstrap_stdio_utf8, safe_print

LOG_DIR = ROOT / "logs" / "branch1_regression"
STATE = ROOT / "tests" / "fixtures" / "branch_state.json"

PRIOR_BRANCH1 = {
    "date": "2026-06-22",
    "s0b": {
        "gap_count": 20,
        "weak_count": 3,
        "pipeline_ok": True,
        "fc_mode": "corpus",
    },
    "s0c": {
        "bridge_count": 1,
        "pipeline_ok": True,
        "cross_doc_label": "교차 1건",
        "merge_mode": "batch_corpus",
    },
}


def _parse_checklists(stdout: str) -> tuple[dict | None, dict | None]:
    s0b, s0c = None, None
    for line in stdout.splitlines():
        if "[S0-B] checklist:" in line:
            m = re.search(r"checklist:\s*(\{.*\})\s*$", line)
            if m:
                try:
                    s0b = json.loads(m.group(1))
                except json.JSONDecodeError:
                    pass
        if "[S0-C] checklist:" in line:
            m = re.search(r"checklist:\s*(\{.*\})\s*$", line)
            if m:
                try:
                    s0c = json.loads(m.group(1))
                except json.JSONDecodeError:
                    pass
    return s0b, s0c


def _normalize_s0b(raw: dict | None) -> dict:
    if not raw:
        return {}
    sk_gap = raw.get("B-2-4_skeleton_gap", raw.get("gap_count"))
    sk_weak = raw.get("B-2-4_skeleton_weak", raw.get("weak_count"))
    return {
        "pipeline_ok": raw.get("B-2-3_pipeline_ok", raw.get("pipeline_ok")),
        "gap_count": sk_gap,
        "weak_count": sk_weak,
        "fc_mode": raw.get("B-2-4_fc_mode", raw.get("fc_mode")),
    }


def _normalize_s0c(raw: dict | None) -> dict:
    if not raw:
        return {}
    return {
        "pipeline_ok": raw.get("C-2-2_merge_mode", raw.get("pipeline_ok")),
        "bridge_count": raw.get("C-2-3_bridge_count", raw.get("bridge_count")),
        "cross_doc_label": raw.get("C-2-4_cross_doc_label", raw.get("cross_doc_label")),
        "merge_mode": "batch_corpus" if raw.get("C-2-2_merge_mode") else raw.get("merge_mode"),
    }


def _delta(current: dict, prior: dict) -> dict:
    out: dict = {}
    for k, pv in prior.items():
        cv = current.get(k)
        if cv != pv:
            out[k] = {"prior": pv, "current": cv}
    return out


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-run", action="store_true", help="do not execute (for tests)")
    args = ap.parse_args()

    if args.skip_run:
        safe_print("[REG-B1] --skip-run: no execution")
        return 0

    t0 = time.monotonic()
    safe_print("[REG-B1] phase_r_regression")
    phase_r_exit = subprocess.call(
        [sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT
    )
    if phase_r_exit != 0:
        safe_print(f"[REG-B1] ABORT phase_r exit {phase_r_exit}")
        return phase_r_exit

    safe_print("[REG-B1] branch1_full_e2e (Gemini)")
    proc = subprocess.run(
        [sys.executable, "scripts/branch1_full_e2e.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    print(combined, end="")
    branch1_exit = proc.returncode
    duration = round(time.monotonic() - t0, 1)

    s0b_raw, s0c_raw = _parse_checklists(combined)
    s0b = _normalize_s0b(s0b_raw)
    s0c = _normalize_s0c(s0c_raw)

    branch_state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}

    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "phase_r_exit": phase_r_exit,
        "branch1_full_exit": branch1_exit,
        "duration_sec": duration,
        "q1_note": "post Q1 2-pass",
        "s0b": s0b,
        "s0c": s0c,
        "s0b_raw_checklist": s0b_raw,
        "s0c_raw_checklist": s0c_raw,
        "branch_state": {
            "branch_1_complete": branch_state.get("branch_1_complete"),
            "branch_2_unlocked": branch_state.get("branch_2_unlocked"),
        },
        "delta_vs_prior": {
            "s0b": _delta(s0b, PRIOR_BRANCH1["s0b"]),
            "s0c": _delta(s0c, PRIOR_BRANCH1["s0c"]),
        },
        "prior_branch1": PRIOR_BRANCH1,
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = LOG_DIR / f"{stamp}-regression.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(f"[REG-B1] wrote {out_path}")
    safe_print(f"[REG-B1] branch1_full exit={branch1_exit} duration={duration}s")

    if branch1_exit != 0:
        tail = combined.strip().splitlines()[-30:]
        safe_print("[REG-B1] tail:\n" + "\n".join(tail))
        return branch1_exit

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
