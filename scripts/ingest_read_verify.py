#!/usr/bin/env python3
"""
Phase R — ingest read verification CLI (no LLM).

See docs/design/INGEST-FOUNDATION-spec.md

Usage:
  python scripts/ingest_read_verify.py --all
  python scripts/ingest_read_verify.py --fixture s0a
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.print_util import safe_print
from deconstructor.web.extract import (
    document_sources_from_bytes,
    expand_document_sources,
    from_text,
)
from deconstructor.web.ingest_verify import verify_read

FIX = ROOT / "tests" / "fixtures"


def _load_s0a() -> tuple[list, dict[str, str]]:
    pdf = FIX / "s0a_paper.pdf"
    if not pdf.is_file():
        raise FileNotFoundError("missing s0a_paper.pdf")
    raw_bytes = pdf.read_bytes()
    from deconstructor.web.extract import _read_pdf

    raw_text = _read_pdf(raw_bytes)
    sources = document_sources_from_bytes(raw_bytes, pdf.name, "application/pdf")
    return sources, {pdf.name: raw_text}


def _load_s0b() -> tuple[list, dict[str, str]]:
    short = FIX / "s0b_draft_short.txt"
    long = FIX / "s0b_draft_long.txt"
    short_text = short.read_text(encoding="utf-8")
    long_text = long.read_text(encoding="utf-8")
    sources = expand_document_sources("short", from_text(short_text), kind="text", source_file=short.name)
    sources += expand_document_sources("long", from_text(long_text), kind="text", source_file=long.name)
    return sources, {short.name: short_text, long.name: long_text}


def _load_s0c() -> tuple[list, dict[str, str]]:
    paper = FIX / "s0c_paper.txt"
    memo = FIX / "s0c_memo.txt"
    pt = paper.read_text(encoding="utf-8")
    mt = memo.read_text(encoding="utf-8")
    sources = expand_document_sources(paper.name, from_text(pt), kind="document", source_file=paper.name)
    sources += expand_document_sources(memo.name, from_text(mt), kind="document", source_file=memo.name)
    return sources, {paper.name: pt, memo.name: mt}


FIXTURES = {
    "s0a": ("S0-A PDF", _load_s0a),
    "s0b": ("S0-B text", _load_s0b),
    "s0c": ("S0-C multi", _load_s0c),
}


def run_one(key: str) -> int:
    label, loader = FIXTURES[key]
    sources, raw_map = loader()
    report = verify_read(sources, raw_by_file=raw_map)
    safe_print(f"[Phase-R] {label} ({key}) ok={report.ok} blocking={report.blocking}")
    failed = [c for c in report.checks if c.severity == "must" and not c.ok]
    if failed:
        safe_print("  MUST fail: " + json.dumps([{"id": c.id, "detail": c.detail} for c in failed], ensure_ascii=False))
    safe_print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.ok else 1


def main() -> int:
    keys = list(FIXTURES.keys()) if "--all" in sys.argv else []
    for arg in sys.argv[1:]:
        if arg.startswith("--fixture="):
            keys.append(arg.split("=", 1)[1])
        elif arg == "--fixture" and len(sys.argv) > sys.argv.index(arg) + 1:
            keys.append(sys.argv[sys.argv.index(arg) + 1])
    if not keys and "--all" not in sys.argv:
        safe_print("Usage: ingest_read_verify.py --all | --fixture s0a|s0b|s0c")
        return 2
    if "--all" in sys.argv:
        keys = list(FIXTURES.keys())
    rc = 0
    for k in keys:
        if k not in FIXTURES:
            safe_print(f"Unknown fixture: {k}")
            rc = 2
            continue
        rc = max(rc, run_one(k))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
