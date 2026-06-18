#!/usr/bin/env python3
"""
Granular skeleton smoke test - dry-run pipeline, Pydantic, routing, trace.

Run:
    python test_run.py
    python test_run.py "B발전소 화재"
    python test_run.py --matrix
    python test_run.py --phase 8
    python test_run.py --phase 1 5 13
    python test_run.py --json

No OpenAI API key, no Neo4j required.
"""

from __future__ import annotations

import argparse
import sys

from deconstructor.cli.print_util import safe_print
from tests.smoke.harness import StepRunner
from tests.smoke.orchestrator import (
    default_headline,
    dump_json,
    run_depth_cap_only,
    run_full_suite,
)
from tests.smoke.registry import phase_labels, phase_numbers, run_phases


def _format_phase_help() -> str:
    lines = [f"  {n:2d}  {phase_labels()[n]}" for n in phase_numbers()]
    return "phase numbers:\n" + "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Granular dry-run smoke test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_format_phase_help(),
    )
    parser.add_argument("headline", nargs="?", default=default_headline())
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--depth-cap", action="store_true")
    parser.add_argument(
        "--phase",
        type=int,
        nargs="+",
        metavar="N",
        help="run only these phase number(s), e.g. --phase 8 or --phase 1 5 13",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run = StepRunner()
    headline = args.headline

    print("=" * 60)
    print("  DECONSTRUCTOR test_run.py - granular smoke test")
    print("=" * 60)

    try:
        report: str | None = None

        if args.phase:
            report = run_phases(run, args.phase, headline)
            if report:
                print(f"\n== phase {args.phase[-1]} report ==")
                safe_print(report)
        elif args.depth_cap:
            report = run_depth_cap_only(run)
            safe_print(report)
            run.check("report printed", True)
        else:
            report = run_full_suite(run, headline, matrix=args.matrix)
            safe_print(report)
            run.check("report printed", True)

        if args.json:
            depth_cap = args.depth_cap or (args.phase == [8])
            print(dump_json(depth_cap=depth_cap, headline=headline))

    except Exception as exc:
        print(f"\n[ABORT] {exc}")
        print(f"  passed={run.passed} failed={run.failed}")
        return 1

    print("\n" + "=" * 60)
    print(f"  ALL CHECKS PASSED ({run.passed} assertions)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
