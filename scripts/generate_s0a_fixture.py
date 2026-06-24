#!/usr/bin/env python3
"""Generate S0-A multi-page paper PDF fixture (A-2-1 ingest, F0-A2 guard safe)."""

from __future__ import annotations

from pathlib import Path

try:
    from fpdf import FPDF
except ImportError as exc:
    raise SystemExit("pip install fpdf2") from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "s0a_paper.pdf"

PAGES = [
    (
        "Ni Catalyst Activity in Methane Reforming",
        "Ni catalyst loading increased from 2 wt% to 5 wt% across batch experiments. "
        "The reactor temperature rose from 650 C to 720 C during the first hour. "
        "Grid power supply remained stable at 220 V throughout the baseline period.",
    ),
    (
        "Reaction Rate and Yield",
        "Reaction rate rose sharply after catalyst activation. "
        "CH4 conversion increased from 45 percent to 78 percent. "
        "Secondary products decreased when pressure was reduced.",
    ),
    (
        "Heat Transfer and Efficiency",
        "Heat input to the reformer increased due to exothermic side reactions. "
        "Thermal efficiency improved when insulation was upgraded. "
        "Coolant flow rate decreased slightly at peak load.",
    ),
    (
        "Conclusions",
        "Overall yield increased under optimized Ni catalyst conditions. "
        "The strongest causal chain links catalyst activation to reaction rate and final yield. "
        "Further work should verify upstream feed composition effects.",
    ),
]


def main() -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for title, body in PAGES:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 8, title)
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, body)
        # Pad page so char count stays high per page
        pdf.ln(6)
        pdf.multi_cell(0, 6, body)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(PAGES)} pages)")


if __name__ == "__main__":
    main()
