#!/usr/bin/env python3
"""
Dreamer Flash breadth probe (μ-DR-DIV-02/03) — one Flash call per run.

  python scripts/dreamer_breadth_probe.py --fixture s0a
  python scripts/dreamer_breadth_probe.py --fixture s0a --runs 3

Deconstruct once per fixture (source facts), then Flash breadth N times.
Output: logs/dreamer_breadth/{fixture}-YYYYMMDD-HHMM[-runN].json
Summary (--runs >1): logs/dreamer_breadth/{fixture}-YYYYMMDD-HHMM-summary.json
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
from deconstructor.agents.dreamer.schemas import DreamHypothesis
from deconstructor.deconstruct.llm_runner import invoke_fact_list
from deconstructor.print_util import bootstrap_stdio_utf8, safe_print
from deconstructor.web.extract import _read_pdf, from_text

LOG_DIR = ROOT / "logs" / "dreamer_breadth"
FIXTURES = {
    "s0a": ROOT / "tests" / "fixtures" / "s0a_paper.pdf",
    "s0b": ROOT / "tests" / "fixtures" / "s0b_draft_short.txt",
}


def _load_text(fixture: str) -> tuple[str, str]:
    path = FIXTURES[fixture]
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}")
    if fixture == "s0a":
        raw = _read_pdf(path.read_bytes())
        return path.name, raw
    return path.name, from_text(path.read_text(encoding="utf-8"))


def _source_facts(text: str) -> list:
    from deconstructor.models import AtomicFact

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


def _run_once(
    fixture: str,
    source_facts: list,
    headline: str,
    *,
    run_index: int | None,
    stamp: str,
) -> dict:
    broad = invoke_flash_breadth(source_facts, headline=headline)
    metrics = diversity_metrics(broad.hypotheses)
    payload = {
        "fixture": fixture,
        "run_index": run_index,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "headline": headline,
        "source_fact_count": len(source_facts),
        "hypothesis_count": len(broad.hypotheses),
        "metrics": metrics,
        "subjects": [h.subject for h in broad.hypotheses],
    }
    suffix = f"-run{run_index}" if run_index is not None else ""
    out = LOG_DIR / f"{fixture}-{stamp}{suffix}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    safe_print(f"[breadth-probe] wrote {out.name} dup={metrics['exact_duplicate_rate']:.3f} "
               f"uniq_subj={metrics['unique_subject_ratio']:.3f}")
    return payload


def _average(runs: list[dict]) -> dict[str, float]:
    keys = ("exact_duplicate_rate", "unique_subject_ratio", "mechanism_similarity_mean")
    out: dict[str, float] = {}
    for k in keys:
        vals = [r["metrics"][k] for r in runs]
        out[k] = sum(vals) / len(vals) if vals else 0.0
    return out


def main() -> int:
    bootstrap_stdio_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", choices=("s0a", "s0b"), default="s0a")
    ap.add_argument("--runs", type=int, default=1, help="Flash breadth repetitions (reuse deconstruct)")
    args = ap.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    name, text = _load_text(args.fixture)
    headline = f"Fixture {args.fixture}: {name}"
    safe_print(f"[breadth-probe] deconstruct once for {name} ({len(text)} chars)")
    source_facts = _source_facts(text)
    safe_print(f"[breadth-probe] source_facts={len(source_facts)}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    runs: list[dict] = []
    for i in range(1, args.runs + 1):
        safe_print(f"[breadth-probe] Flash breadth run {i}/{args.runs}")
        runs.append(_run_once(args.fixture, source_facts, headline, run_index=i if args.runs > 1 else None, stamp=stamp))

    if args.runs > 1:
        summary = {
            "fixture": args.fixture,
            "runs": args.runs,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "averages": _average(runs),
            "runs_detail": [r["metrics"] for r in runs],
        }
        sum_path = LOG_DIR / f"{args.fixture}-{stamp}-summary.json"
        sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        safe_print(f"[breadth-probe] summary {sum_path.name} avg={summary['averages']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
