#!/usr/bin/env python3
"""
S0-C manual E2E — 다중 파일 교차 因→과 (STAGE-0-2 C-2-*).

See docs/design/STAGE-0-CLOSURE-spec.md (μ-C-*)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print
from deconstructor.web.extract import expand_document_sources, from_text
from scripts.e2e_common import fail_or_pass, run_batch

PAPER = ROOT / "tests" / "fixtures" / "s0c_paper.txt"
MEMO = ROOT / "tests" / "fixtures" / "s0c_memo.txt"


def _sources(path: Path) -> list:
    text = from_text(path.read_text(encoding="utf-8"))
    return expand_document_sources(path.name, text, kind="document", source_file=path.name)


def main() -> int:
    ingest_only = "--ingest-only" in sys.argv

    if not PAPER.is_file() or not MEMO.is_file():
        safe_print("Missing fixtures - run: python scripts/generate_s0bc_fixtures.py")
        return 1

    sources = _sources(PAPER) + _sources(MEMO)
    files = {s.source_file for s in sources}

    c21 = len(files) >= 2 and len(sources) >= 2
    safe_print(f"[S0-C] ingest sources={len(sources)} files={sorted(files)}")

    if ingest_only:
        checklist = {
            "C-2-1_multi_file_ingest": c21,
            "source_files": sorted(files),
            "chunk_counts": {f: sum(1 for s in sources if s.source_file == f) for f in files},
            "pipeline_skipped": True,
            "reason": "ingest-only mode (mu-C-ING complete)",
        }
        from scripts.e2e_common import print_checklist

        print_checklist("S0-C", checklist)
        if not c21:
            safe_print("[S0-C] FAIL: ingest AC")
            return 3
        safe_print(f"[S0-C] PASS (ingest-only) - files={sorted(files)}")
        return 0

    result, _ = run_batch(sources)
    orch = result.get("orchestration") or {}
    bridge = orch.get("bridge_count", 0)
    label = orch.get("cross_doc_label", "")

    c22 = orch.get("merge_mode") == "batch_corpus"
    c24 = bool(label) and ("교차" in label)
    c23 = bridge >= 0  # explicit 0 or N per AC-ORC-02

    checklist = {
        "C-2-1_multi_file_ingest": c21,
        "C-2-2_merge_mode": c22,
        "C-2-3_bridge_count": bridge,
        "C-2-3_bridge_explicit": c23,
        "C-2-4_cross_doc_label": label,
        "C-2-4_ui_label_ok": c24,
        "pipeline_ok": result.get("ok") is True,
        "nodes": result.get("nodes"),
        "edges": result.get("edges"),
        "source_files": orch.get("source_files"),
    }

    if not c21 or not c22 or not c24:
        from scripts.e2e_common import print_checklist

        print_checklist("S0-C", checklist)
        safe_print("[S0-C] FAIL: orchestration AC")
        return 3

    return fail_or_pass(
        "S0-C",
        result,
        checklist,
        pass_detail=f"bridge={bridge} label={label} files={len(files)}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
