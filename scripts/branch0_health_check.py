#!/usr/bin/env python3
"""
μ-MAINT-02 — Branch-0 health check (offline + Phase R, LLM 0).

μ-ID: μ-MAINT-02 (wave μ-MAINT-ω)
선행: Branch-0 MUST active; ingest touch 시 μ-MAINT-R
실행: python scripts/branch0_health_check.py
스펙: docs/design/BRANCH-0-MAINTENANCE-spec.md

순서: stage0_reaudit_baseline → phase_r_regression → pytest (branch_gates + ingest_foundation)
산출: logs/branch0_health/YYYYMMDD-HHMM-health.json

금지: branch1_full_e2e, b2a_density live, capability probe live.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import bootstrap_stdio_utf8, safe_print

LOG_DIR = ROOT / "logs" / "branch0_health"
BASELINE_DIR = ROOT / "logs" / "stage0_reaudit"


def _run_step(name: str, cmd: list[str]) -> dict:
    rc = subprocess.call(cmd, cwd=ROOT)
    return {"step": name, "exit_code": rc, "command": " ".join(cmd)}


def _pytest_branch0() -> dict:
    py = sys.executable
    cmd = [
        py,
        "-m",
        "pytest",
        "tests/test_branch_gates.py",
        "tests/test_ingest_foundation.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = ((proc.stdout or "") + (proc.stderr or "")).strip()
    m_pass = re.search(r"(\d+) passed", tail)
    m_fail = re.search(r"(\d+) failed", tail)
    return {
        "step": "pytest_branch_gates_ingest",
        "exit_code": proc.returncode,
        "command": " ".join(cmd),
        "passed": int(m_pass.group(1)) if m_pass else 0,
        "failed": int(m_fail.group(1)) if m_fail else 0,
        "tail": tail[-400:],
    }


def _latest_baseline_mismatches() -> tuple[list, str | None]:
    if not BASELINE_DIR.is_dir():
        return [], None
    files = sorted(BASELINE_DIR.glob("*-baseline.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return [], None
    path = files[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("mismatches") or []), str(path.relative_to(ROOT))


def main() -> int:
    bootstrap_stdio_utf8()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = LOG_DIR / f"{stamp}-health.json"

    steps: list[dict] = []

    baseline = _run_step(
        "stage0_reaudit_baseline",
        [sys.executable, "scripts/stage0_reaudit_baseline.py"],
    )
    steps.append(baseline)
    mismatches, baseline_ref = _latest_baseline_mismatches()
    baseline["baseline_ref"] = baseline_ref
    baseline["mismatches"] = mismatches

    phase_r = _run_step(
        "phase_r_regression",
        [sys.executable, "scripts/phase_r_regression.py"],
    )
    steps.append(phase_r)

    pytest_step = _pytest_branch0()
    steps.append(pytest_step)

    ok = all(s["exit_code"] == 0 for s in steps) and not mismatches
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mu_id": "μ-MAINT-02",
        "ok": ok,
        "steps": steps,
        "mismatches": mismatches,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(json.dumps(payload, indent=2, ensure_ascii=False))
    safe_print(f"\n[Branch-0 health] wrote {out_path}")
    if ok:
        safe_print("[Branch-0 health] PASS")
        return 0
    safe_print("[Branch-0 health] FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
