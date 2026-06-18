#!/usr/bin/env python3
"""
Granular skeptic smoke test - rule-by-rule correlation vs causation.

Run:
    python test_skeptic_run.py
    python test_skeptic_run.py --report
    python test_skeptic_run.py --phase 3
    python test_skeptic_run.py --phase 1 6 --report

No OpenAI API key required.
"""

from __future__ import annotations

import argparse

from tests.smoke.harness import StepRunner
from tests.smoke.skeptic.orchestrator import run_skeptic_suite
from tests.smoke.skeptic.registry import skeptic_phase_labels, skeptic_phase_numbers


def _format_phase_help() -> str:
    lines = [f"  {n:2d}  {skeptic_phase_labels()[n]}" for n in skeptic_phase_numbers()]
    return "skeptic phase numbers:\n" + "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Granular skeptic smoke test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_format_phase_help(),
    )
    parser.add_argument(
        "--phase",
        type=int,
        nargs="+",
        metavar="N",
        help="run only these phase number(s), e.g. --phase 3 or --phase 1 6",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="append phase 8 (formatted skeptic batch report)",
    )
    args = parser.parse_args(argv)

    run = StepRunner()
    print("=" * 60)
    print("  test_skeptic_run.py - granular skeptic verification")
    print("=" * 60)

    try:
        run_skeptic_suite(
            run,
            with_report=args.report,
            phases=args.phase,
        )
    except Exception as exc:
        print(f"\n[ABORT] {exc}")
        print(f"  passed={run.passed} failed={run.failed}")
        return 1

    print("\n" + "=" * 60)
    print(f"  ALL SKEPTIC CHECKS PASSED ({run.passed} assertions)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
