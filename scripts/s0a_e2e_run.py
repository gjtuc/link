#!/usr/bin/env python3
"""
S0-A manual E2E — 논문 PDF 1편 (STAGE-0-2 A-2-*).

Runs ingest + full pipeline_batch; prints AC checklist JSON.
See docs/design/S0-A-E2E-RECORD.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print

FIXTURE = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"
CHAR_RETENTION_MIN = 0.95


def main() -> int:
    if not FIXTURE.is_file():
        safe_print("Missing fixture - run: python scripts/generate_s0a_fixture.py")
        return 1

    from deconstructor import config
    from deconstructor.web.extract import document_sources_from_bytes
    from deconstructor.web.link_steps import LinkStepTracker
    from deconstructor.web.pipeline_batch import run_pipeline_batch

    raw = FIXTURE.read_bytes()
    sources = document_sources_from_bytes(raw, FIXTURE.name, "application/pdf")
    total_chars = sum(len(s.text) for s in sources)
    raw_len = len(raw)  # PDF bytes — use extracted text sum vs itself for ratio proxy

    # A-2-1: no summarize — extracted text substantial
    a21 = total_chars >= 500 and len(sources) >= 1
    a21_detail = {
        "sources": len(sources),
        "total_extracted_chars": total_chars,
        "labels": [s.label for s in sources[:5]],
        "document_page_count": sources[0].document_page_count if sources else 0,
    }

    safe_print(
        ("[S0-A] ingest OK" if a21 else "[S0-A] ingest FAIL")
        + " "
        + json.dumps(a21_detail, ensure_ascii=False)
    )

    tracker = LinkStepTracker()
    result = run_pipeline_batch(sources, tracker=tracker)

    fc = result.get("fact_checker") or {}
    sk = result.get("skeleton") or {}
    rc = result.get("recompose") or {}
    watch = result.get("watch") or {}

    checklist = {
        "A-2-1_ingest_no_summarize": a21,
        "A-2-2_pipeline_ok": result.get("ok") is True,
        "A-2-2_completed_facts_total": result.get("atomic_facts_total", 0),
        "A-2-3_nodes": result.get("nodes", 0),
        "A-2-3_edges": result.get("edges", 0),
        "A-2-4_fact_checker_mode": fc.get("mode"),
        "A-2-4_corpus_or_stub": fc.get("mode") in ("corpus", "stub"),
        "A-2-5_skeleton_gap": sk.get("gap_count"),
        "A-2-5_skeleton_strong": sk.get("strong_chain_count"),
        "A-2-5_recompose": bool(rc.get("report_markdown")),
        "partial_run": watch.get("has_partial_run"),
        "failed_step": result.get("failed_step"),
    }

    safe_print("[S0-A] checklist: " + json.dumps(checklist, ensure_ascii=False, indent=2))

    if not result.get("ok"):
        safe_print(f"[S0-A] FAIL: {result.get('message')} {result.get('failed_step')}")
        return 2

    # A-2-5: NG-2 — nodes exist; skeleton metrics present
    a25 = sk.get("gap_count") is not None and sk.get("strong_chain_count") is not None
    if not a25:
        safe_print("[S0-A] A-2-5 skeleton missing")
        return 3

    safe_print(
        f"[S0-A] PASS - fact_checker={fc.get('mode')} nodes={result.get('nodes')} "
        f"gap={sk.get('gap_count')} strong={sk.get('strong_chain_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
