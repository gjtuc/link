#!/usr/bin/env python3
"""
μ-PROBE-00 — capability catalog live probes.

μ-ID: μ-PROBE-00~03, μ-PROBE-SCAN-R2a/R2b
선행: phase_r_regression exit 0
실행:
  python scripts/capability_catalog_probe.py neo4j-off
  python scripts/capability_catalog_probe.py pdf-triple
  python scripts/capability_catalog_probe.py scanned-pdf [--path <pdf>] [--skip-phase-r]
스펙: docs/design/CAPABILITY-PROBE-spec.md

neo4j-off: NEO4J_URI=bolt://127.0.0.1:19999 로 bolt 불가 강제 후 short text Phase A.
scanned-pdf: R2a (0-char scan_no_text_layer) / R2b (scan_ocr_noisy) 관측 — detail JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# neo4j-off: env before deconstructor import (config.NEO4J_URI)
if len(sys.argv) > 1 and sys.argv[1] == "neo4j-off":
    os.environ["NEO4J_URI"] = "bolt://127.0.0.1:19999"

sys.path.insert(0, str(ROOT))

from deconstructor.print_util import bootstrap_stdio_utf8, safe_print
from deconstructor.web.extract import _read_pdf, document_sources_from_bytes, expand_document_sources, from_text
from deconstructor.web.ingest_verify import verify_read
from scripts.e2e_common import run_batch
from scripts.log_capability_run import log_capability_run

SCRIPT_NAME = "capability_catalog_probe.py"
DETAIL_DIR = ROOT / "logs" / "capability_probes"
PROBE_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "capability_probes"

CAT_NEO4J = "cat-neo4j-off"
CAT_PDF_TRIPLE = "cat-pdf-triple"
CAT_SCANNED = "cat-scanned-pdf"

SHORT_FIXTURE = ROOT / "tests" / "fixtures" / "s0b_draft_short.txt"
S0A_PDF = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"


def ensure_phase_r(*, skip: bool = False) -> int:
    if skip:
        return 0
    return subprocess.call([sys.executable, "scripts/phase_r_regression.py"], cwd=ROOT)


def _neo4j_available() -> bool:
    from deconstructor.viz.neo4j_utils import neo4j_is_available

    return neo4j_is_available()


def _write_detail(cat_id: str, detail: dict) -> Path:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    safe_id = cat_id.replace("/", "-")
    path = DETAIL_DIR / f"{stamp}-{safe_id}-detail.json"
    path.write_text(json.dumps(detail, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _pdf_probe_stats(data: bytes) -> tuple[int, int]:
    from deconstructor.web.extract import _read_pdf_pages

    pages = _read_pdf_pages(data)
    return sum(len(p) for p in pages), len(pages)


def _failure_class(
    *,
    pipeline_ok: bool,
    failed_step: str | None,
    message: str | None,
    phase_r_block: bool = False,
    read_verify_block: bool = False,
) -> str:
    if phase_r_block:
        return "phase_r_block"
    if read_verify_block:
        return "read_verify_fail"
    if pipeline_ok:
        return "pipeline_ok"
    blob = f"{failed_step or ''} {message or ''}".lower()
    if "503" in blob or "unavailable" in blob:
        return "gemini_503"
    if "429" in blob:
        return "gemini_429"
    return "pipeline_fail"


def _finish(cat_id: str, exit_code: int, detail: dict, *, probe_meta: dict | None = None) -> int:
    if probe_meta:
        detail = {**detail, **probe_meta}
    detail.setdefault("exit_code", exit_code)
    detail_path = _write_detail(cat_id, detail)
    run_path = log_capability_run(cat_id, SCRIPT_NAME, exit_code)
    safe_print(f"[probe] detail {detail_path}")
    safe_print(f"[probe] run log {run_path}")
    safe_print(f"[probe] {cat_id} exit={exit_code}")
    return exit_code


def _run_probe(
    cat_id: str,
    scenario: str,
    sources: list,
    *,
    raw_by_file: dict[str, str] | None = None,
    files: list[str],
    neo4j_method: str = "",
    skip_phase_r: bool = False,
    probe_meta: dict | None = None,
) -> int:
    t0 = time.monotonic()
    pr = ensure_phase_r(skip=skip_phase_r)
    if pr != 0:
        detail = {
            "scenario": scenario,
            "cat_id": cat_id,
            "files": files,
            "phase_r_exit": pr,
            "neo4j_available": _neo4j_available(),
            "neo4j_method": neo4j_method,
            "pipeline_ok": False,
            "failed_step": "phase_r_regression",
            "failure_class": _failure_class(pipeline_ok=False, failed_step="phase_r_regression", message=None, phase_r_block=True),
            "elapsed_sec": round(time.monotonic() - t0, 1),
        }
        return _finish(cat_id, 1, detail, probe_meta=probe_meta)

    read_report = verify_read(sources, raw_by_file=raw_by_file)
    if not read_report.ok:
        detail = {
            "scenario": scenario,
            "cat_id": cat_id,
            "files": files,
            "phase_r_ok": False,
            "neo4j_available": _neo4j_available(),
            "neo4j_method": neo4j_method,
            "pipeline_ok": False,
            "failed_step": "read_verify",
            "failure_class": _failure_class(pipeline_ok=False, failed_step="read_verify", message=None, read_verify_block=True),
            "elapsed_sec": round(time.monotonic() - t0, 1),
        }
        return _finish(cat_id, 2, detail, probe_meta=probe_meta)

    result, tracker, _ = run_batch(
        sources,
        scenario=scenario,
        raw_by_file=raw_by_file,
        read_only=False,
    )
    elapsed = round(time.monotonic() - t0, 1)
    pipeline_ok = bool(result and result.get("ok"))
    failed_step = None if pipeline_ok else (result or {}).get("failed_step")
    message = (result or {}).get("message") or (result or {}).get("error")
    if not pipeline_ok and tracker:
        for rec in reversed(tracker.steps):
            if rec.status == "error" and rec.detail:
                message = message or rec.detail
                break
    distinct_sources = sorted({getattr(s, "source_file", "") or "" for s in sources})
    link_disable = os.getenv("LINK_DISABLE_NEO4J_AUTO_START", "").lower() in ("1", "true", "yes")
    detail = {
        "scenario": scenario,
        "cat_id": cat_id,
        "files": files,
        "distinct_source_files": distinct_sources,
        "phase_r_ok": True,
        "neo4j_available": _neo4j_available(),
        "neo4j_method": neo4j_method,
        "link_disable_neo4j_auto_start": link_disable,
        "pipeline_ok": pipeline_ok,
        "failed_step": failed_step,
        "failure_class": _failure_class(pipeline_ok=pipeline_ok, failed_step=failed_step, message=message),
        "elapsed_sec": elapsed,
        "nodes": (result or {}).get("nodes"),
        "edges": (result or {}).get("edges"),
        "message": message,
    }
    if tracker and tracker.failed_step:
        detail["link_failed_step"] = tracker.failed_step
    exit_code = 0 if pipeline_ok else 2
    return _finish(cat_id, exit_code, detail, probe_meta=probe_meta)


def cmd_neo4j_off(_args: argparse.Namespace) -> int:
    from deconstructor import config

    os.environ["LINK_DISABLE_NEO4J_AUTO_START"] = "1"
    config.NEO4J_URI = "bolt://127.0.0.1:19999"
    if not SHORT_FIXTURE.is_file():
        safe_print(f"Missing {SHORT_FIXTURE}")
        return 1
    text = SHORT_FIXTURE.read_text(encoding="utf-8")
    sources = expand_document_sources(
        "short", from_text(text), kind="text", source_file=SHORT_FIXTURE.name
    )
    return _run_probe(
        CAT_NEO4J,
        "PROBE-neo4j-off",
        sources,
        raw_by_file={SHORT_FIXTURE.name: text},
        files=[str(SHORT_FIXTURE.name)],
        neo4j_method="NEO4J_URI=bolt://127.0.0.1:19999",
        skip_phase_r=getattr(_args, "skip_phase_r", False),
    )


def cmd_pdf_triple(_args: argparse.Namespace) -> int:
    if not S0A_PDF.is_file():
        safe_print("Missing s0a_paper.pdf — run: python scripts/generate_s0a_fixture.py")
        return 1
    PROBE_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    names = ("file-a.pdf", "file-b.pdf", "file-c.pdf")
    raw_bytes = S0A_PDF.read_bytes()
    sources = []
    raw_map: dict[str, str] = {}
    files: list[str] = []
    for name in names:
        dest = PROBE_FIXTURE_DIR / name
        dest.write_bytes(raw_bytes)
        files.append(name)
        text = _read_pdf(raw_bytes)
        raw_map[name] = text
        sources.extend(document_sources_from_bytes(raw_bytes, name, "application/pdf"))
    return _run_probe(
        CAT_PDF_TRIPLE,
        "PROBE-pdf-triple",
        sources,
        raw_by_file=raw_map,
        files=files,
        skip_phase_r=getattr(_args, "skip_phase_r", False),
    )


def _find_scanned_pdf(explicit: str | None) -> tuple[Path | None, str]:
    if explicit:
        p = Path(explicit)
        return (p, "cli") if p.is_file() else (None, "cli_missing")
    for pattern in ("*scan*.pdf", "*scanned*.pdf"):
        for p in (ROOT / "tests" / "fixtures").glob(pattern):
            return p, "fixtures"
    search_roots = [
        Path.home() / "Desktop",
        ROOT / ".cursor" / "KCH",
        ROOT.parent,
    ]
    for base in search_roots:
        if not base.is_dir():
            continue
        try:
            for p in base.rglob("*.pdf"):
                low = p.name.lower()
                if "scan" in low or "scanned" in low:
                    return p, f"discovered:{base}"
        except OSError:
            continue
    return None, "not_found"


def cmd_scanned_pdf(args: argparse.Namespace) -> int:
    t0 = time.monotonic()
    path, origin = _find_scanned_pdf(args.path)
    if path is None:
        if not S0A_PDF.is_file():
            return 1
        pr = ensure_phase_r(skip=getattr(args, "skip_phase_r", False))
        raw_bytes = S0A_PDF.read_bytes()
        text = _read_pdf(raw_bytes)
        sources = document_sources_from_bytes(raw_bytes, "not-true-scan.pdf", "application/pdf")
        read_ok = verify_read(sources, raw_by_file={"not-true-scan.pdf": text}).ok
        detail = {
            "scenario": "PROBE-scanned-pdf",
            "cat_id": CAT_SCANNED,
            "files": ["not-true-scan.pdf"],
            "scan_origin": origin,
            "not_true_scan": True,
            "phase_r_ok": read_ok,
            "neo4j_available": _neo4j_available(),
            "pipeline_ok": False,
            "failed_step": "no_true_scan_pdf",
            "elapsed_sec": round(time.monotonic() - t0, 1),
            "phase_r_exit": pr,
        }
        safe_print("[probe] no true scan PDF — text-born fallback, exit 2")
        return _finish(CAT_SCANNED, 2, detail)

    raw_bytes = path.read_bytes()
    pypdf_chars, page_count = _pdf_probe_stats(raw_bytes)
    text = _read_pdf(raw_bytes)
    name = path.name
    probe_meta: dict | None = None
    if pypdf_chars == 0:
        probe_meta = {
            "mu_id": "μ-PROBE-SCAN-R2a",
            "pdf_class": "scan_no_text_layer",
            "pypdf_extract_chars": pypdf_chars,
            "page_count": page_count,
        }
        pr = ensure_phase_r(skip=getattr(args, "skip_phase_r", False))
        failure_class = "phase_r_block" if pr != 0 else "empty_extract"
        detail = {
            "scenario": "PROBE-scanned-pdf",
            "cat_id": CAT_SCANNED,
            "files": [name],
            "scan_origin": origin,
            "phase_r_ok": pr == 0,
            "phase_r_exit": pr,
            "neo4j_available": _neo4j_available(),
            "neo4j_method": f"origin={origin}",
            "pipeline_ok": False,
            "failed_step": "empty_extract",
            "failure_class": failure_class,
            "elapsed_sec": round(time.monotonic() - t0, 1),
        }
        safe_print(
            f"[probe] scan_no_text_layer — pypdf 0 chars / {page_count}p, exit 2"
        )
        return _finish(CAT_SCANNED, 2, detail, probe_meta=probe_meta)

    if pypdf_chars > 1000:
        probe_meta = {
            "mu_id": "μ-PROBE-SCAN-R2b",
            "pdf_class": "scan_ocr_noisy",
            "pypdf_extract_chars": pypdf_chars,
            "page_count": page_count,
        }
        safe_print(
            f"[probe] scan_ocr_noisy — pypdf {pypdf_chars} chars / {page_count}p"
        )

    sources = document_sources_from_bytes(raw_bytes, name, "application/pdf")
    return _run_probe(
        CAT_SCANNED,
        "PROBE-scanned-pdf",
        sources,
        raw_by_file={name: text},
        files=[name],
        neo4j_method=f"origin={origin}",
        skip_phase_r=getattr(args, "skip_phase_r", False),
        probe_meta=probe_meta,
    )


def _add_skip_phase_r(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skip-phase-r",
        action="store_true",
        help="batch: phase_r already run",
    )


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser(description="Capability catalog live probes")
    _add_skip_phase_r(ap)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_neo = sub.add_parser("neo4j-off", help="Neo4j bolt unavailable + short text Phase A")
    _add_skip_phase_r(p_neo)
    p_pdf = sub.add_parser("pdf-triple", help="3 PDF batch Phase A")
    _add_skip_phase_r(p_pdf)
    sp = sub.add_parser("scanned-pdf", help="scanned/image PDF ingest probe")
    _add_skip_phase_r(sp)
    sp.add_argument("--path", default="", help="explicit PDF path")
    args = ap.parse_args()
    if args.cmd == "neo4j-off":
        return cmd_neo4j_off(args)
    if args.cmd == "pdf-triple":
        return cmd_pdf_triple(args)
    if args.cmd == "scanned-pdf":
        return cmd_scanned_pdf(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
