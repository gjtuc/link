#!/usr/bin/env python3
"""
μ-B2-00 — unlock Branch-2a after catalog probes.

선행: branch_1_complete=true, probe logs cat-neo4j-off / cat-pdf-triple / cat-scanned-pdf
실행: python scripts/unlock_branch2.py
스펙: docs/design/BRANCH-2a-spec.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "tests" / "fixtures" / "branch_state.json"
LOG_DIR = ROOT / "logs" / "capability_runs"

REQUIRED_PROBE_IDS = frozenset({"cat-neo4j-off", "cat-pdf-triple", "cat-scanned-pdf"})


def _probe_ids_present() -> tuple[set[str], set[str]]:
    found: set[str] = set()
    if not LOG_DIR.is_dir():
        return found, REQUIRED_PROBE_IDS
    for path in LOG_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        pid = data.get("id")
        if pid in REQUIRED_PROBE_IDS:
            found.add(pid)
    return found, REQUIRED_PROBE_IDS - found


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if not state.get("branch_1_complete"):
        print("[unlock] ABORT: branch_1_complete must be true")
        return 1
    found, missing = _probe_ids_present()
    if missing:
        print(f"[unlock] ABORT: missing probe logs for {sorted(missing)} (found {sorted(found)})")
        return 1
    state["branch_2_unlocked"] = True
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("[unlock] branch_2_unlocked=true (Branch-2a)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
