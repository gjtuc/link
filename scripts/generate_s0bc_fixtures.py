#!/usr/bin/env python3
"""Generate S0-B / S0-C text fixtures (STAGE-0-CLOSURE μ-FIX-*)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"

S0B_SHORT = """\
Executive Summary

Revenue will increase significantly next quarter because market conditions are favorable.
Our product is well positioned and customers are satisfied.

Background

The team held three meetings in January. Several slides were updated.
Competitor activity was noted in the trade press.

Analysis

Sales figures from last year were reviewed. The dashboard shows green indicators.
Management believes growth is likely.

Conclusion

Therefore we recommend proceeding with the expansion plan immediately.
"""

S0B_LONG_PARA = (
    "Section {n}: The report discusses operational metrics, stakeholder feedback, "
    "and projected outcomes without establishing clear upstream causes for the conclusion. "
    "Meeting notes reference activity levels, document revisions, and survey summaries. "
)

S0C_PAPER = """\
Ni Catalyst Study — Primary Document

Ni catalyst loading was increased from 2 wt% to 5 wt% in the reformer experiments.
Reactor temperature rose from 650 C to 720 C during activation.
CH4 conversion increased from 45 percent to 78 percent after catalyst activation.
Heat input increased due to exothermic side reactions in the secondary loop.
Overall yield improved under optimized Ni catalyst conditions at 700 C.
"""

S0C_MEMO = """\
Lab Memo — Supplementary Notes

Ni catalyst particle size grew from 3.5 nm to 10.5 nm when loading exceeded 4 wt%.
Grid power supply remained stable during overnight runs.
Ni catalyst surface area decreased slightly after the third regeneration cycle.
Coolant flow was reduced at peak thermal load.
"""


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)

    short_path = FIX / "s0b_draft_short.txt"
    short_path.write_text(S0B_SHORT.strip() + "\n", encoding="utf-8")

    long_body = S0B_SHORT.strip() + "\n\n" + "".join(S0B_LONG_PARA.format(n=i) for i in range(1, 45))
    long_path = FIX / "s0b_draft_long.txt"
    long_path.write_text(long_body, encoding="utf-8")

    (FIX / "s0c_paper.txt").write_text(S0C_PAPER.strip() + "\n", encoding="utf-8")
    (FIX / "s0c_memo.txt").write_text(S0C_MEMO.strip() + "\n", encoding="utf-8")

    print(f"Wrote {short_path} ({len(S0B_SHORT)} chars)")
    print(f"Wrote {long_path} ({len(long_body)} chars)")
    print(f"Wrote s0c_paper.txt, s0c_memo.txt")


if __name__ == "__main__":
    main()
