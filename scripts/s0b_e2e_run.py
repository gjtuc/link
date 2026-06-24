#!/usr/bin/env python3
"""S0-B E2E — Phase R (read) then Phase A (analyze). See INGEST-FOUNDATION-spec.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print
from deconstructor.web.extract import expand_document_sources, from_text
from scripts.e2e_common import fail_or_pass, print_checklist, run_batch

SHORT = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
LONG = ROOT / "tests" / "fixtures" / "s0b_draft_long.txt"


def main() -> int:
    read_only = "--read-only" in sys.argv or "--ingest-only" in sys.argv

    if not SHORT.is_file() or not LONG.is_file():
        safe_print("Missing fixtures - run: python scripts/generate_s0bc_fixtures.py")
        return 1

    short_text = SHORT.read_text(encoding="utf-8")
    long_text = LONG.read_text(encoding="utf-8")
    short_src = expand_document_sources("short", from_text(short_text), kind="text", source_file=SHORT.name)
    long_src = expand_document_sources("long", from_text(long_text), kind="text", source_file=LONG.name)
    sources = short_src + long_src
    raw_map = {SHORT.name: short_text, LONG.name: long_text}

    result, _, read_report = run_batch(
        sources,
        scenario="S0-B",
        raw_by_file=raw_map,
        read_only=read_only,
    )

    if not read_report.ok:
        print_checklist("S0-B", {"Phase-R": read_report.to_dict()})
        safe_print("[S0-B] FAIL Phase-R")
        return 2

    if read_only:
        print_checklist(
            "S0-B",
            {
                "Phase-R_ok": True,
                "short_chunks": len(short_src),
                "long_chunks": len(long_src),
                "Phase-A_skipped": True,
            },
        )
        safe_print(f"[S0-B] PASS Phase-R - short=1 long={len(long_src)}")
        return 0

    assert result is not None
    sk = result.get("skeleton") or {}
    fc = result.get("fact_checker") or {}
    checklist = {
        "Phase-R_ok": True,
        "B-2-3_pipeline_ok": result.get("ok") is True,
        "B-2-4_skeleton_gap": sk.get("gap_count"),
        "B-2-4_skeleton_weak": sk.get("weak_count"),
        "B-2-4_fc_mode": fc.get("mode"),
    }
    if sk.get("gap_count") is None:
        print_checklist("S0-B", checklist)
        safe_print("[S0-B] FAIL Phase-A skeleton")
        return 4

    return fail_or_pass(
        "S0-B",
        result,
        checklist,
        pass_detail=f"gap={sk.get('gap_count')} weak={sk.get('weak_count')}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
