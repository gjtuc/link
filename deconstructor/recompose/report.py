"""
Sprint 6 — ε-2 skeleton health report (SP6-RPT-01~03).
"""

from __future__ import annotations

NG3_DISCLAIMER = (
    "NG-3: 본 리포트는 검증·가설·기각 출처를 표시할 뿐, "
    "논문·보고서의 진실을 보장하지 않습니다 (δ)."
)


def build_health_report(
    skeleton: dict,
    *,
    fact_checker: dict | None = None,
) -> str:
    """Markdown health report from skeleton index (RPT-01, RPT-02)."""
    hs = skeleton.get("health_summary") or {}
    gap_n = hs.get("gap_count", skeleton.get("gap_count", 0))
    strong_n = hs.get("strong_chain_count", skeleton.get("strong_chain_count", 0))
    weak_n = hs.get("weak_count", skeleton.get("weak_count", 0))
    fc_mode = (fact_checker or {}).get("mode", "unknown")

    lines = [
        "# Skeleton Health Report (ε-2)",
        "",
        "## Summary",
        f"- **Gap** (빈 因): {gap_n}",
        f"- **Strong** chains: {strong_n}",
        f"- **Weak**: {weak_n}",
        f"- Fact-Checker mode: `{fc_mode}`",
        "",
    ]

    gaps = skeleton.get("gaps") or []
    if gaps:
        lines.append("## Gaps (빈 因)")
        for g in gaps:
            lines.append(
                f"- **{g.get('subject', '?')}** — {g.get('state_change', '')} "
                f"(`{g.get('reason', 'gap')}`)"
            )
        lines.append("")

    chains = skeleton.get("strong_chains") or []
    if chains:
        lines.append("## Strong Chains (verified CAUSES ≥2)")
        for i, ch in enumerate(chains, 1):
            labels = ch.get("labels") or ch.get("node_ids") or []
            joined = " → ".join(str(x) for x in labels)
            lines.append(f"{i}. {joined} (length={ch.get('length', '?')})")
        lines.append("")

    weak = skeleton.get("weak") or []
    if weak:
        lines.append("## Weak / Hypothesis")
        for w in weak[:20]:
            lines.append(
                f"- {w.get('subject', '?')} — {w.get('reason', 'weak')}"
            )
        if len(weak) > 20:
            lines.append(f"- … and {len(weak) - 20} more")
        lines.append("")

    lines.extend(["## Disclaimer", NG3_DISCLAIMER, ""])
    return "\n".join(lines)
