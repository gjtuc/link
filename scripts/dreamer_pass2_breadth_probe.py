#!/usr/bin/env python3
"""
V5 — 2-pass pass2 Flash breadth probe (μ-V5-01).

Deconstruct → skeptic_pass1 (live) → select_pass2_source_facts → Flash × N.

  python scripts/dreamer_pass2_breadth_probe.py --fixture s0b --runs 3
  python scripts/dreamer_pass2_breadth_probe.py --fixture s0a --runs 3

Output: logs/dreamer_breadth/pass2-{fixture}-YYYYMMDD-HHMM[-runN].json
        logs/dreamer_breadth/pass2-{fixture}-YYYYMMDD-HHMM-summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deconstructor.agents.dreamer.diversity import diversity_metrics
from deconstructor.agents.dreamer.llm_runner import invoke_flash_breadth
from deconstructor.agents.dreamer.pass2_inputs import select_pass2_source_facts
from deconstructor.deconstruct.llm_runner import invoke_fact_list
from deconstructor.models import AtomicFact
from deconstructor.pipeline.state_factory import make_initial_state
from deconstructor.print_util import bootstrap_stdio_utf8, safe_print
from deconstructor.skeptic.pass1_node import skeptic_pass1_node
from deconstructor.web.extract import _read_pdf, from_text

LOG_DIR = ROOT / "logs" / "dreamer_breadth"
FIXTURES = {
    "s0a": ROOT / "tests" / "fixtures" / "s0a_paper.pdf",
    "s0b": ROOT / "tests" / "fixtures" / "s0b_draft_short.txt",
}

DIV03_THRESHOLDS = {
    "exact_duplicate_rate_max": 0.10,
    "unique_subject_ratio_min": 0.70,
    "mechanism_similarity_mean_max": 0.15,
}


def _load_text(fixture: str) -> tuple[str, str]:
    path = FIXTURES[fixture]
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}")
    if fixture == "s0a":
        raw = _read_pdf(path.read_bytes())
        return path.name, raw
    return path.name, from_text(path.read_text(encoding="utf-8"))


def _completed_facts(text: str) -> list[AtomicFact]:
    result = invoke_fact_list(text)
    facts: list[AtomicFact] = []
    for f in result.facts:
        facts.append(
            AtomicFact(
                id=f.id,
                subject=f.subject,
                state_change=f.state_change,
                timestamp=f.timestamp,
                is_atomic=True,
                source_type="extracted",
                check_status="active",
            )
        )
    return facts


def _preview_sources(sources: list[AtomicFact], limit: int = 80) -> list[dict]:
    out: list[dict] = []
    for f in sources:
        sc = f.state_change or ""
        out.append(
            {
                "id": f.id,
                "subject": f.subject,
                "state_change_preview": sc[:limit] + ("…" if len(sc) > limit else ""),
            }
        )
    return out


def _pass1_state(headline: str, completed: list[AtomicFact]) -> dict:
    state = make_initial_state(headline, enable_dreamer=True)
    state["completed_facts"] = completed
    state["extracted_facts"] = []
    state["recursion_depth"] = 1
    return state


def _average(runs: list[dict]) -> dict[str, float]:
    keys = ("exact_duplicate_rate", "unique_subject_ratio", "mechanism_similarity_mean")
    out: dict[str, float] = {}
    for k in keys:
        vals = [r["metrics"][k] for r in runs]
        out[k] = sum(vals) / len(vals) if vals else 0.0
    return out


def _threshold_verdict(avg: dict[str, float]) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True
    if avg.get("exact_duplicate_rate", 1.0) > DIV03_THRESHOLDS["exact_duplicate_rate_max"]:
        ok = False
        notes.append(f"dup {avg['exact_duplicate_rate']:.3f} > {DIV03_THRESHOLDS['exact_duplicate_rate_max']}")
    if avg.get("unique_subject_ratio", 0.0) < DIV03_THRESHOLDS["unique_subject_ratio_min"]:
        ok = False
        notes.append(f"unique_subj {avg['unique_subject_ratio']:.3f} < {DIV03_THRESHOLDS['unique_subject_ratio_min']}")
    if avg.get("mechanism_similarity_mean", 1.0) > DIV03_THRESHOLDS["mechanism_similarity_mean_max"]:
        ok = False
        notes.append(f"mech_sim {avg['mechanism_similarity_mean']:.3f} > {DIV03_THRESHOLDS['mechanism_similarity_mean_max']}")
    return ok, notes


def _run_flash_once(
    fixture: str,
    pass2_sources: list[AtomicFact],
    headline: str,
    meta: dict,
    *,
    run_index: int | None,
    stamp: str,
) -> dict:
    broad = invoke_flash_breadth(pass2_sources, headline=headline)
    metrics = diversity_metrics(broad.hypotheses)
    payload = {
        "mode": "2pass_pass2",
        "fixture": fixture,
        "run_index": run_index,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "headline": headline,
        **meta,
        "pass2_source_ids": [f.id for f in pass2_sources],
        "hypothesis_count": len(broad.hypotheses),
        "metrics": metrics,
        "subjects": [h.subject for h in broad.hypotheses],
    }
    suffix = f"-run{run_index}" if run_index is not None else ""
    out = LOG_DIR / f"pass2-{fixture}-{stamp}{suffix}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(
        f"[pass2-probe] wrote {out.name} dup={metrics['exact_duplicate_rate']:.3f} "
        f"uniq_subj={metrics['unique_subject_ratio']:.3f} mech_sim={metrics['mechanism_similarity_mean']:.3f}"
    )
    return payload


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser(description="V5 2-pass pass2 Flash breadth probe")
    ap.add_argument("--fixture", choices=("s0a", "s0b"), default="s0b")
    ap.add_argument("--runs", type=int, default=3, help="Flash breadth repetitions on same pass2 sources")
    ap.add_argument(
        "--skeptic-dry-run",
        action="store_true",
        help="skeptic_pass1 retry stub (default: live retry)",
    )
    args = ap.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    name, text = _load_text(args.fixture)
    headline = f"Fixture {args.fixture}: {name}"

    safe_print(f"[pass2-probe] deconstruct for {name} ({len(text)} chars)")
    completed = _completed_facts(text)
    safe_print(f"[pass2-probe] completed_facts={len(completed)}")

    state = _pass1_state(headline, completed)
    pass1_out = skeptic_pass1_node(state, dry_run=args.skeptic_dry_run)
    edges = pass1_out.get("verified_edges_pass1") or []
    gaps = pass1_out.get("pass2_gap_nodes") or []
    pass2_sources = select_pass2_source_facts(completed, edges, gap_nodes=gaps)

    meta = {
        "pass1_edge_count": len(edges),
        "pass2_gap_count": len(gaps),
        "pass2_source_count": len(pass2_sources),
        "deconstruct_fact_count": len(completed),
        "pass2_sources_preview": _preview_sources(pass2_sources),
    }
    safe_print(
        f"[pass2-probe] pass1_edges={meta['pass1_edge_count']} "
        f"gaps={meta['pass2_gap_count']} pass2_sources={meta['pass2_source_count']}"
    )

    if not pass2_sources:
        safe_print("[pass2-probe] ABORT: no pass2 sources after pass1")
        return 1

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    runs: list[dict] = []
    for i in range(1, args.runs + 1):
        safe_print(f"[pass2-probe] Flash breadth run {i}/{args.runs}")
        runs.append(
            _run_flash_once(
                args.fixture,
                pass2_sources,
                headline,
                meta,
                run_index=i if args.runs > 1 else None,
                stamp=stamp,
            )
        )

    if args.runs > 1:
        averages = _average(runs)
        passed, notes = _threshold_verdict(averages)
        summary = {
            "mode": "2pass_pass2",
            "fixture": args.fixture,
            "runs": args.runs,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "pass1_edge_count": meta["pass1_edge_count"],
            "pass2_gap_count": meta["pass2_gap_count"],
            "pass2_source_count": meta["pass2_source_count"],
            "deconstruct_fact_count": meta["deconstruct_fact_count"],
            "averages": averages,
            "runs_detail": [r["metrics"] for r in runs],
            "div03_thresholds": DIV03_THRESHOLDS,
            "div03_pass": passed,
            "div03_notes": notes,
        }
        sum_path = LOG_DIR / f"pass2-{args.fixture}-{stamp}-summary.json"
        sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        verdict = "PASS" if passed else "FAIL"
        safe_print(f"[pass2-probe] summary {sum_path.name} avg={averages} → DIV03 {verdict}")
        if notes:
            for n in notes:
                safe_print(f"  - {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
