#!/usr/bin/env python3
"""
S0-B manual E2E — 보고서 초안 텍스트 (STAGE-0-2 B-2-*).

See docs/design/STAGE-0-CLOSURE-spec.md (μ-B-*)
"""

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


def _sources(path: Path, label: str) -> list:
    text = from_text(path.read_text(encoding="utf-8"))
    return expand_document_sources(label, text, kind="text", source_file=path.name)


def main() -> int:
    ingest_only = "--ingest-only" in sys.argv

    if not SHORT.is_file() or not LONG.is_file():
        safe_print("Missing fixtures - run: python scripts/generate_s0bc_fixtures.py")
        return 1

    short_src = _sources(SHORT, "텍스트 #1 (short)")
    long_src = _sources(LONG, "텍스트 #2 (long)")

    b21 = len(short_src) == 1 and len(short_src[0].text) >= 200
    b22 = len(long_src) >= 2
    b22_chars = sum(len(s.text) for s in long_src)
    b22_no_summarize = b22_chars >= 8000

    safe_print(
        f"[S0-B] ingest-only short_chunks={len(short_src)} long_chunks={len(long_src)} "
        f"long_chars={b22_chars}"
    )

    if not b21 or not b22 or not b22_no_summarize:
        checklist = {
            "B-2-1_short_single_chunk": b21,
            "B-2-2_long_multi_chunk": b22,
            "B-2-2_no_summarize": b22_no_summarize,
        }
        print_checklist("S0-B", checklist)
        safe_print("[S0-B] FAIL: ingest AC")
        return 3

    if ingest_only:
        checklist = {
            "B-2-1_short_single_chunk": b21,
            "B-2-2_long_multi_chunk": b22,
            "B-2-2_long_chars": b22_chars,
            "pipeline_skipped": True,
            "reason": "ingest-only mode (mu-B-ING complete)",
        }
        print_checklist("S0-B", checklist)
        safe_print(f"[S0-B] PASS (ingest-only) - short=1 long={len(long_src)} chars={b22_chars}")
        return 0

    # Pipeline on weak short draft only (μ-B-PIPE)
    result, _ = run_batch(short_src)
    sk = result.get("skeleton") or {}
    fc = result.get("fact_checker") or {}
    rc = result.get("recompose") or {}

    gap = sk.get("gap_count")
    weak = sk.get("weak_count")
    b24 = gap is not None and sk.get("strong_chain_count") is not None

    checklist = {
        "B-2-1_short_single_chunk": b21,
        "B-2-2_long_multi_chunk": b22,
        "B-2-2_long_chars": b22_chars,
        "B-2-3_pipeline_ok": result.get("ok") is True,
        "B-2-3_edges": result.get("edges"),
        "B-2-4_skeleton_gap": gap,
        "B-2-4_skeleton_weak": weak,
        "B-2-4_skeleton_metrics": b24,
        "B-2-4_recompose": bool(rc.get("report_markdown")),
        "B-2-4_fc_mode": fc.get("mode"),
    }

    if not b24:
        print_checklist("S0-B", checklist)
        safe_print("[S0-B] FAIL: skeleton metrics missing")
        return 4

    return fail_or_pass(
        "S0-B",
        result,
        checklist,
        pass_detail=f"gap={gap} weak={weak} fc={fc.get('mode')}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
