"""
Sprint 7 — F0-A2 ingest guard (SP7-ING-01~03, AC-ING-07).

Detects document PDF with many pages but suspiciously few extracted chars.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deconstructor.web.extract import ExtractedSource

F0_A2_MIN_PAGES = 3
F0_A2_MAX_CHARS = 500


@dataclass(frozen=True)
class IngestGuardResult:
    blocking: bool
    violations: list[dict]
    message: str = ""

    def to_watch_dict(self) -> dict:
        return {
            "blocking": self.blocking,
            "f0_a2_violations": self.violations,
            "message": self.message,
        }


def _aggregate_pdf_sources(sources: list[ExtractedSource]) -> dict[str, dict]:
    by_file: dict[str, dict] = {}
    for src in sources:
        key = (src.source_file or src.label or "").strip()
        if not key:
            continue
        bucket = by_file.setdefault(
            key,
            {"chars": 0, "page_count": 0, "kind": src.kind, "labels": []},
        )
        bucket["chars"] += len(src.text or "")
        bucket["page_count"] = max(bucket["page_count"], int(src.document_page_count or 0))
        bucket["kind"] = src.kind
        bucket["labels"].append(src.label)
    return by_file


def detect_f0_a2_violations(sources: list[ExtractedSource]) -> list[dict]:
    """
    F0-A2 symptom: PDF pages>3 but total chars<500 (likely summarize or bad OCR).
    """
    violations: list[dict] = []
    for source_file, agg in _aggregate_pdf_sources(sources).items():
        pages = agg["page_count"]
        chars = agg["chars"]
        if pages <= F0_A2_MIN_PAGES:
            continue
        if chars >= F0_A2_MAX_CHARS:
            continue
        violations.append(
            {
                "code": "F0-A2",
                "source_file": source_file,
                "page_count": pages,
                "total_chars": chars,
                "message": (
                    f"F0-A2: {source_file} — PDF {pages}페이지인데 추출 문자 {chars}자 "
                    f"(<{F0_A2_MAX_CHARS}). summarize/추출 실패 의심 (NG-1)."
                ),
            }
        )
    return violations


def check_f0_a2_blocking(sources: list[ExtractedSource]) -> IngestGuardResult:
    """Return blocking result when F0-A2 violations present (AC-ING-07)."""
    violations = detect_f0_a2_violations(sources)
    if not violations:
        return IngestGuardResult(blocking=False, violations=[])
    msg = violations[0]["message"]
    if len(violations) > 1:
        msg += f" (+{len(violations) - 1}건)"
    return IngestGuardResult(blocking=True, violations=violations, message=msg)
