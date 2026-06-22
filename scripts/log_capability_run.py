#!/usr/bin/env python3
"""
μ-Q2-05 — capability probe / E2E run log.

실행: python scripts/log_capability_run.py --id cap-s0b-draft --script s0b_e2e_run.py --exit 0
스펙: docs/design/Q2-CAPABILITIES-spec.md
선행: Q2 capabilities build (human_line lookup)

Writes: logs/capability_runs/YYYYMMDD-HHMM-<id>.json (gitignore)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.capabilities import build_capabilities

LOG_DIR = ROOT / "logs" / "capability_runs"


def _human_line_for(cap_id: str) -> str:
    payload = build_capabilities(ROOT)
    for cap in payload.get("capabilities", []):
        if cap.get("id") == cap_id:
            return str(cap.get("human_line", ""))
    return ""


def log_capability_run(
    cap_id: str,
    script: str,
    exit_code: int,
    *,
    human_line: str | None = None,
    root: Path | None = None,
) -> Path:
    base = root or ROOT
    line = human_line if human_line is not None else _human_line_for(cap_id)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    safe_id = cap_id.replace("/", "-")
    out = base / "logs" / "capability_runs" / f"{stamp}-{safe_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "id": cap_id,
        "script": script,
        "exit_code": exit_code,
        "human_line": line,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="capability id")
    ap.add_argument("--script", required=True, help="script name")
    ap.add_argument("--exit", type=int, default=0, dest="exit_code")
    ap.add_argument("--human-line", default="", help="override human_line")
    args = ap.parse_args()
    line = args.human_line or None
    path = log_capability_run(args.id, args.script, args.exit_code, human_line=line)
    print(f"[cap-run] wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
