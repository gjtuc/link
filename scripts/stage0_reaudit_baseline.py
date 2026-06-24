#!/usr/bin/env python3
"""
μ-POST-Q2-0 / STAGE 0 re-audit baseline (ω-0) — LLM-free gate snapshot.

μ-ID: μ-POST-Q2-0b — ω-0 baseline 확장 (Q1/Q2 pytest + capabilities)
선행: Q2 c472879, Branch-1 complete
실행: python scripts/stage0_reaudit_baseline.py
스펙: docs/design/Q2-CAPABILITIES-spec.md § μ-POST-Q2-0

Output: logs/stage0_reaudit/YYYYMMDD-HHMM-baseline.json
Exit 1 if mismatches non-empty or any gate fails.
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

from deconstructor.capabilities import build_capabilities
from deconstructor.print_util import bootstrap_stdio_utf8, safe_print

DESIGN = ROOT / "docs" / "design"
STATE_FILE = ROOT / "tests" / "fixtures" / "branch_state.json"
LOG_DIR = ROOT / "logs" / "stage0_reaudit"

Q1_TESTS = (
    "tests/test_q1_pass2_inputs.py",
    "tests/test_q1_two_pass_dry_run.py",
)
Q2_TESTS = (
    "tests/test_capabilities_build.py",
    "tests/test_capabilities_api.py",
)


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=ROOT)


def _pytest_summary(test_paths: str | tuple[str, ...]) -> dict:
    paths = (test_paths,) if isinstance(test_paths, str) else test_paths
    py = sys.executable
    proc = subprocess.run(
        [py, "-m", "pytest", *paths, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tail = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"(\d+) passed", tail)
    f = re.search(r"(\d+) failed", tail)
    return {
        "exit_code": proc.returncode,
        "passed": int(m.group(1)) if m else 0,
        "failed": int(f.group(1)) if f else 0,
        "tail": tail.strip()[-500:],
    }


def _record_phase_a(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.search(r"\|\s*\*\*A\*\*\s*\|\s*1\s*\|\s*([^|]+)\|", text)
    return m.group(1).strip() if m else None


def _closure_row(closure_id: str) -> str | None:
    spec = (DESIGN / "STAGE-0-CLOSURE-spec.md").read_text(encoding="utf-8")
    m = re.search(rf"\|\s*\*\*{re.escape(closure_id)}\*\*[^\n]+\|", spec)
    return m.group(0).strip() if m else None


def _mismatches(
    state: dict,
    records: dict[str, str | None],
    closures: dict[str, str | None],
    *,
    caps_summary: dict[str, int],
    caps_total: int,
) -> list[str]:
    out: list[str] = []
    b1 = state.get("branch_1_complete")
    if not b1:
        out.append("branch_1_complete=false (expected true after Branch-1)")
    if state.get("branch_2_unlocked") and not b1:
        out.append("branch_2_unlocked=true but branch_1_complete=false")
    for cid, record_a in records.items():
        closure = closures.get(cid) or ""
        if b1 and record_a and "PASS" not in record_a and "✅" not in record_a:
            out.append(f"{cid}: branch_1_complete=true but RECORD Phase A={record_a!r}")
        if b1 and "A⏸" in closure:
            out.append(f"{cid}: branch_1_complete=true but CLOSURE-spec still A⏸")
        if b1 and "A✅" in (record_a or "") and "A⏸" in closure:
            out.append(f"{cid}: RECORD Phase A ✅ but CLOSURE-spec still A⏸")
    if caps_summary.get("verified", 0) < 1:
        out.append("q2_capabilities: verified < 1")
    if caps_total < 10:
        out.append(f"q2_capabilities: total={caps_total} < 10")
    return out


def main() -> int:
    bootstrap_stdio_utf8()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = LOG_DIR / f"{stamp}-baseline.json"

    phase_r_rc = _run([sys.executable, "scripts/phase_r_regression.py"])

    pytest_gates = _pytest_summary("tests/test_branch_gates.py")
    pytest_ingest = _pytest_summary("tests/test_ingest_foundation.py")
    pytest_stage0 = _pytest_summary("tests/test_stage0_acceptance.py")
    pytest_q1 = _pytest_summary(Q1_TESTS)
    pytest_q2 = _pytest_summary(Q2_TESTS)

    caps_payload = build_capabilities(ROOT)
    caps_summary = caps_payload.get("summary", {})
    caps_total = len(caps_payload.get("capabilities", []))

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    records = {
        "CL-0-B": _record_phase_a(DESIGN / "S0-B-E2E-RECORD.md"),
        "CL-0-C": _record_phase_a(DESIGN / "S0-C-E2E-RECORD.md"),
    }
    closures = {
        "CL-0-B": _closure_row("CL-0-B"),
        "CL-0-C": _closure_row("CL-0-C"),
    }
    mismatches = _mismatches(
        state,
        records,
        closures,
        caps_summary=caps_summary,
        caps_total=caps_total,
    )

    if phase_r_rc != 0:
        mismatches.append(f"phase_r_regression exit {phase_r_rc}")
    for name, result in (
        ("test_branch_gates", pytest_gates),
        ("test_ingest_foundation", pytest_ingest),
        ("test_stage0_acceptance", pytest_stage0),
        ("pytest_q1", pytest_q1),
        ("pytest_q2", pytest_q2),
    ):
        if result["exit_code"] != 0:
            mismatches.append(f"{name} exit {result['exit_code']}")

    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "branch_state": state,
        "phase_r_regression_exit": phase_r_rc,
        "pytest": {
            "test_branch_gates": pytest_gates,
            "test_ingest_foundation": pytest_ingest,
            "test_stage0_acceptance": pytest_stage0,
        },
        "pytest_q1": pytest_q1,
        "pytest_q2": pytest_q2,
        "q2_capabilities": {
            "verified": caps_summary.get("verified", 0),
            "untested": caps_summary.get("untested", 0),
            "unsupported": caps_summary.get("unsupported", 0),
            "total": caps_total,
        },
        "record_phase_a": records,
        "closure_spec_rows": closures,
        "mismatches": mismatches,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(json.dumps(payload, indent=2, ensure_ascii=False))
    safe_print(f"\n[reaudit] wrote {out_path}")

    if mismatches:
        safe_print(f"[reaudit] FAIL mismatches={mismatches}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
