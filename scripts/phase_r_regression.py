#!/usr/bin/env python3
"""
Phase R regression — ingest touch MUST gate (LLM 0).

When INGEST_TOUCH_PATHS change, run this script before commit.
See tests/ingest_manifest.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import bootstrap_stdio_utf8, safe_print


def _run(label: str, cmd: list[str]) -> int:
    safe_print(f"\n=== Phase-R: {label} ===")
    safe_print("  " + " ".join(cmd))
    rc = subprocess.call(cmd, cwd=ROOT)
    if rc != 0:
        safe_print(f"[Phase-R] FAIL at: {label} (exit {rc})")
    else:
        safe_print(f"[Phase-R] OK: {label}")
    return rc


def main() -> int:
    bootstrap_stdio_utf8()
    py = sys.executable
    rc = 0

    rc = max(
        rc,
        _run(
            "pytest branch gates",
            [py, "-m", "pytest", "tests/test_branch_gates.py", "-q"],
        ),
    )
    rc = max(
        rc,
        _run(
            "pytest ingest+stage0",
            [py, "-m", "pytest", "tests/test_ingest_foundation.py", "tests/test_stage0_acceptance.py", "-q"],
        ),
    )
    rc = max(rc, _run("ingest_read_verify --all", [py, "scripts/ingest_read_verify.py", "--all"]))

    for script in ("s0a_e2e_run.py", "s0b_e2e_run.py", "s0c_e2e_run.py"):
        rc = max(
            rc,
            _run(f"{script} --read-only", [py, f"scripts/{script}", "--read-only"]),
        )

    if rc == 0:
        safe_print("\n[Phase-R] ALL PASS - safe to proceed (Phase A when quota allows)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
