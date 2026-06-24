"""
Ingest foundation — Phase R (읽기 확인) before Phase A (분석 확인).

See ``docs/design/INGEST-FOUNDATION-spec.md`` (μ-R-* → μ-A-*).

LLM / Deconstruct MUST NOT run until ``verify_read().ok`` is True.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from deconstructor.guards.ingest_guard import check_f0_a2_blocking
from deconstructor.provenance.source_meta import make_chunk_id
from deconstructor.web.document_chunks import DOC_CHUNK_CHARS
from deconstructor.web.extract import (
    DOCUMENT_INGEST_MODE,
    MAX_HEADLINE_CHARS,
    _DOC_SUMMARIZE_THRESHOLD,
    _use_document_deconstruct_ingest,
)

if TYPE_CHECKING:
    from deconstructor.web.extract import ExtractedSource

CHAR_RETENTION_MIN = 0.95
LONG_DOC_CHARS = 8_000
SHORT_TEXT_MAX_CHARS = 2_000


@dataclass
class ReadCheck:
    """Single μ-R check outcome."""

    id: str
    ok: bool
    detail: str = ""
    severity: str = "must"  # must | should


@dataclass
class ReadVerifyReport:
    """Phase R aggregate — gate for Phase A."""

    ok: bool
    blocking: bool
    checks: list[ReadCheck] = field(default_factory=list)
    message: str = ""

    @property
    def must_failed(self) -> list[ReadCheck]:
        return [c for c in self.checks if c.severity == "must" and not c.ok]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blocking": self.blocking,
            "message": self.message,
            "checks": [
                {"id": c.id, "ok": c.ok, "detail": c.detail, "severity": c.severity}
                for c in self.checks
            ],
            "passed": sum(1 for c in self.checks if c.ok),
            "total": len(self.checks),
        }


def _add(checks: list[ReadCheck], id: str, ok: bool, detail: str = "", *, severity: str = "must") -> None:
    checks.append(ReadCheck(id=id, ok=ok, detail=detail, severity=severity))


def _sources_by_file(sources: list[ExtractedSource]) -> dict[str, list[ExtractedSource]]:
    by_file: dict[str, list[ExtractedSource]] = {}
    for src in sources:
        key = (src.source_file or src.label or "unknown").strip()
        by_file.setdefault(key, []).append(src)
    return by_file


def verify_read(
    sources: list[ExtractedSource],
    *,
    raw_by_file: dict[str, str] | None = None,
    require_document_mode: bool = True,
) -> ReadVerifyReport:
    """
    Phase R — 읽기 확인 (offline, no LLM).

    ``raw_by_file``: optional map ``source_file -> raw extracted text`` for μ-R-RET-01.
    """
    checks: list[ReadCheck] = []

    # μ-R-MODE
    if require_document_mode:
        mode_ok = _use_document_deconstruct_ingest()
        _add(
            checks,
            "μ-R-MODE-01",
            mode_ok,
            f"LINK_DOCUMENT_INGEST={DOCUMENT_INGEST_MODE}",
        )
    else:
        _add(checks, "μ-R-MODE-01", True, "skipped", severity="should")

    # μ-R-EXT
    if not sources:
        _add(checks, "μ-R-EXT-01", False, "no sources")
        return ReadVerifyReport(ok=False, blocking=True, checks=checks, message="소스 없음")

    empty = [s.label for s in sources if not (s.text or "").strip()]
    _add(checks, "μ-R-EXT-01", not empty, f"empty={empty[:3]}" if empty else f"n={len(sources)}")

    by_file = _sources_by_file(sources)
    total_chars = sum(len(s.text or "") for s in sources)

    # μ-R-RET
    if raw_by_file:
        for file_key, raw in raw_by_file.items():
            raw_len = len((raw or "").strip())
            if raw_len == 0:
                continue
            got = sum(len(s.text or "") for s in by_file.get(file_key, []))
            if not got and file_key in by_file:
                got = sum(len(s.text or "") for s in by_file[file_key])
            ratio = got / raw_len if raw_len else 0.0
            _add(
                checks,
                "μ-R-RET-01",
                ratio >= CHAR_RETENTION_MIN,
                f"{file_key} ratio={ratio:.3f} ({got}/{raw_len})",
            )
    else:
        _add(checks, "μ-R-RET-01", True, "no raw reference (skipped)", severity="should")

    _add(
        checks,
        "μ-R-RET-02",
        total_chars >= 50 or len(sources) == 1,
        f"total_chars={total_chars}",
    )

    guard = check_f0_a2_blocking(sources)
    _add(
        checks,
        "μ-R-GUARD-01",
        not guard.blocking,
        guard.message or "F0-A2 clear",
    )

    # μ-R-CHK per file
    for file_key, file_sources in by_file.items():
        file_chars = sum(len(s.text or "") for s in file_sources)
        n = len(file_sources)

        if file_chars > LONG_DOC_CHARS:
            _add(
                checks,
                f"μ-R-CHK-01:{file_key}",
                n >= 2,
                f"chars={file_chars} chunks={n}",
            )
        else:
            _add(
                checks,
                f"μ-R-CHK-01:{file_key}",
                True,
                f"short doc chunks={n}",
                severity="should",
            )

        if file_chars <= SHORT_TEXT_MAX_CHARS:
            _add(
                checks,
                f"μ-R-CHK-04:{file_key}",
                n == 1,
                f"short={file_chars}c chunks={n}",
            )

        for i, src in enumerate(file_sources):
            label = src.label or ""
            has_label = ("청크" in label) or ("p." in label) or (" · " in label) or n == 1
            _add(
                checks,
                f"μ-R-CHK-02:{file_key}:{i}",
                has_label,
                label[:60],
                severity="should" if n == 1 else "must",
            )

            chunk_len = len(src.text or "")
            max_allowed = min(DOC_CHUNK_CHARS, MAX_HEADLINE_CHARS) + 500
            _add(
                checks,
                f"μ-R-CHK-03:{file_key}:{i}",
                chunk_len <= max_allowed,
                f"len={chunk_len}",
            )

    # μ-R-META
    doc_kinds = {"document", "text"}
    for i, src in enumerate(sources):
        if src.kind in doc_kinds:
            _add(
                checks,
                f"μ-R-META-01:{i}",
                bool((src.source_file or "").strip()),
                src.label[:40],
            )
        expected_id = make_chunk_id(
            src.source_file or src.label,
            src.chunk_index,
            src.chunk_total,
        )
        _add(
            checks,
            f"μ-R-META-02:{i}",
            src.chunk_id == expected_id,
            src.chunk_id,
            severity="should",
        )
        _add(
            checks,
            f"μ-R-META-03:{i}",
            1 <= src.chunk_index <= src.chunk_total,
            f"{src.chunk_index}/{src.chunk_total}",
            severity="should",
        )

    for file_key, file_sources in by_file.items():
        totals = {s.chunk_total for s in file_sources}
        _add(
            checks,
            f"μ-R-META-03b:{file_key}",
            len(totals) == 1,
            f"totals={sorted(totals)}",
            severity="should",
        )

    # μ-R-BAT
    if len(by_file) >= 2:
        _add(
            checks,
            "μ-R-BAT-01",
            len(by_file) >= 2,
            f"files={sorted(by_file.keys())}",
        )

    must_fail = [c for c in checks if c.severity == "must" and not c.ok]
    blocking = guard.blocking or bool(must_fail)
    ok = not blocking and not must_fail
    msg = ""
    if guard.blocking:
        msg = guard.message
    elif must_fail:
        msg = must_fail[0].id + ": " + must_fail[0].detail

    return ReadVerifyReport(ok=ok, blocking=blocking, checks=checks, message=msg)
