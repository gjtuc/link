#!/usr/bin/env python3
"""
S0-A manual E2E — 논문 PDF 1편.

Phase R (읽기 확인) → Phase A (분석 확인).
See docs/design/INGEST-FOUNDATION-spec.md, S0-A-E2E-RECORD.md
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print
from deconstructor.web.extract import _read_pdf, document_sources_from_bytes
from scripts.e2e_common import fail_or_pass, print_checklist, run_batch

FIXTURE = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"


def main() -> int:
    read_only = "--read-only" in sys.argv or "--ingest-only" in sys.argv

    if not FIXTURE.is_file():
        safe_print("Missing fixture - run: python scripts/generate_s0a_fixture.py")
        return 1

    raw_bytes = FIXTURE.read_bytes()
    raw_text = _read_pdf(raw_bytes)
    sources = document_sources_from_bytes(raw_bytes, FIXTURE.name, "application/pdf")
    raw_map = {FIXTURE.name: raw_text}

    result, _, read_report = run_batch(
        sources,
        scenario="S0-A",
        raw_by_file=raw_map,
        read_only=read_only,
    )

    total_chars = sum(len(s.text) for s in sources)
    a21 = total_chars >= 500 and len(sources) >= 1

    if not read_report.ok:
        print_checklist("S0-A", {"Phase-R": read_report.to_dict(), "A-2-1": a21})
        safe_print("[S0-A] FAIL Phase-R (read verify)")
        return 2

    if read_only:
        checklist = {
            "Phase-R_ok": True,
            "A-2-1_ingest_no_summarize": a21,
            "sources": len(sources),
            "total_extracted_chars": total_chars,
            "Phase-A_skipped": True,
        }
        print_checklist("S0-A", checklist)
        safe_print(f"[S0-A] PASS Phase-R - chars={total_chars} sources={len(sources)}")
        return 0

    assert result is not None
    fc = result.get("fact_checker") or {}
    sk = result.get("skeleton") or {}
    rc = result.get("recompose") or {}
    watch = result.get("watch") or {}

    checklist = {
        "Phase-R_ok": True,
        "A-2-1_ingest_no_summarize": a21,
        "A-2-2_pipeline_ok": result.get("ok") is True,
        "A-2-2_completed_facts_total": result.get("atomic_facts_total", 0),
        "A-2-3_nodes": result.get("nodes", 0),
        "A-2-3_edges": result.get("edges", 0),
        "A-2-4_fact_checker_mode": fc.get("mode"),
        "A-2-5_skeleton_gap": sk.get("gap_count"),
        "A-2-5_skeleton_strong": sk.get("strong_chain_count"),
        "A-2-5_recompose": bool(rc.get("report_markdown")),
        "partial_run": watch.get("has_partial_run"),
        "failed_step": result.get("failed_step"),
    }

    if not result.get("ok"):
        print_checklist("S0-A", checklist)
        safe_print("[S0-A] FAIL Phase-A")
        return 3

    a25 = sk.get("gap_count") is not None and sk.get("strong_chain_count") is not None
    if not a25:
        print_checklist("S0-A", checklist)
        safe_print("[S0-A] A-2-5 skeleton missing")
        return 4

    return fail_or_pass(
        "S0-A",
        result,
        checklist,
        pass_detail=f"Phase-A fc={fc.get('mode')} nodes={result.get('nodes')} gap={sk.get('gap_count')}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
