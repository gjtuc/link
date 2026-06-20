"""
Sprint 1 (G-ING-META) — document ingest provenance on AtomicFact (C-2, AC-ING-05).

See ``docs/design/SPRINT-1-ingest-meta-spec.md`` (P-03, L-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def make_chunk_id(source_file: str, chunk_index: int, chunk_total: int) -> str:
    """Stable chunk id: ``{safe_file}#chunk-{i}/{n}`` (μ P-03)."""
    safe = (source_file or "source").replace("#", "_").replace("/", "_").strip()
    idx = max(1, int(chunk_index))
    total = max(1, int(chunk_total))
    return f"{safe}#chunk-{idx}/{total}"


def page_range_from_suffix(suffix: str) -> str:
    """PDF page label ``p.1`` / ``p.1-3`` → page_range field."""
    s = (suffix or "").strip()
    return s if s.startswith("p.") else ""


@dataclass(frozen=True)
class SourceDocumentMeta:
    """Ingest → pipeline → verify stamp (μ L-01)."""

    source_file: str = ""
    page_range: str = ""
    chunk_id: str = ""
    chunk_index: int = 1
    chunk_total: int = 1

    def to_state_dict(self) -> dict[str, str | int]:
        return {
            "source_file": self.source_file,
            "page_range": self.page_range,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any] | None) -> SourceDocumentMeta:
        if not data:
            return cls()
        return cls(
            source_file=str(data.get("source_file") or ""),
            page_range=str(data.get("page_range") or ""),
            chunk_id=str(data.get("chunk_id") or ""),
            chunk_index=int(data.get("chunk_index") or 1),
            chunk_total=int(data.get("chunk_total") or 1),
        )

    def to_fact_update(self) -> dict[str, str]:
        return {
            "source_file": self.source_file,
            "page_range": self.page_range,
            "chunk_id": self.chunk_id,
        }


def meta_from_extracted_fields(
    *,
    source_file: str = "",
    page_range: str = "",
    chunk_id: str = "",
    chunk_index: int = 1,
    chunk_total: int = 1,
) -> SourceDocumentMeta:
    return SourceDocumentMeta(
        source_file=source_file,
        page_range=page_range,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_total=chunk_total,
    )
