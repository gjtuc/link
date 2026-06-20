#!/usr/bin/env python3
"""S0-C E2E — Phase R then Phase A. See INGEST-FOUNDATION-spec.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print
from deconstructor.web.extract import expand_document_sources, from_text
from scripts.e2e_common import fail_or_pass, print_checklist, run_batch

PAPER = ROOT / "tests" / "fixtures" / "s0c_paper.txt"
MEMO = ROOT / "tests" / "fixtures" / "s0c_memo.txt"


def main() -> int:
    read_only = "--read-only" in sys.argv or "--ingest-only" in sys.argv

    if not PAPER.is_file() or not MEMO.is_file():
        safe_print("Missing fixtures - run: python scripts/generate_s0bc_fixtures.py")
        return 1

    pt = PAPER.read_text(encoding="utf-8")
    mt = MEMO.read_text(encoding="utf-8")
    sources = expand_document_sources(PAPER.name, from_text(pt), kind="document", source_file=PAPER.name)
    sources += expand_document_sources(MEMO.name, from_text(mt), kind="document", source_file=MEMO.name)
    raw_map = {PAPER.name: pt, MEMO.name: mt}

    result, _, read_report = run_batch(
        sources,
        scenario="S0-C",
        raw_by_file=raw_map,
        read_only=read_only,
    )

    if not read_report.ok:
        print_checklist("S0-C", {"Phase-R": read_report.to_dict()})
        safe_print("[S0-C] FAIL Phase-R")
        return 2

    if read_only:
        files = {s.source_file for s in sources}
        print_checklist(
            "S0-C",
            {"Phase-R_ok": True, "files": sorted(files), "Phase-A_skipped": True},
        )
        safe_print(f"[S0-C] PASS Phase-R - files={sorted(files)}")
        return 0

    assert result is not None
    orch = result.get("orchestration") or {}
    checklist = {
        "Phase-R_ok": True,
        "C-2-2_merge_mode": orch.get("merge_mode") == "batch_corpus",
        "C-2-3_bridge_count": orch.get("bridge_count"),
        "C-2-4_cross_doc_label": orch.get("cross_doc_label"),
        "pipeline_ok": result.get("ok") is True,
    }

    if orch.get("merge_mode") != "batch_corpus":
        print_checklist("S0-C", checklist)
        safe_print("[S0-C] FAIL Phase-A orchestration")
        return 4

    return fail_or_pass(
        "S0-C",
        result,
        checklist,
        pass_detail=f"bridge={orch.get('bridge_count')} label={orch.get('cross_doc_label')}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
