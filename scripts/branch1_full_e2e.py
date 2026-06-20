#!/usr/bin/env python3
"""
Branch-1 full E2E — quota 복구 후 다음 작업.

Runs S0-B / S0-C Phase A (no --read-only). On success updates branch_state.json.

Prerequisite: python scripts/phase_r_regression.py (Branch-0)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "tests" / "fixtures" / "branch_state.json"


def _run(script: str) -> int:
    cmd = [sys.executable, f"scripts/{script}"]
    print(f"\n=== Branch-1: {script} ===")
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    rc = subprocess.call([sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT)
    if rc != 0:
        print("[Branch-1] ABORT: Branch-0 (phase_r_regression) failed")
        return rc

    for script in ("s0b_e2e_run.py", "s0c_e2e_run.py"):
        rc = max(rc, _run(script))

    if rc == 0:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        state["branch_1_complete"] = True
        STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print("[Branch-1] COMPLETE - branch_state.branch_1_complete=true")
        print("[Branch-1] branch_2_unlocked remains false until explicitly set")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
