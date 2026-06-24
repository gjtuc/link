"""
μ-2b-00 — STAGE-1 cross-run corpus contract (types + validation).

스펙: docs/design/STAGE-1-CORPUS-spec.md
선행: μ-UNLOCK-2b
금지: pipeline_batch DAG 변경 (μ-2b-01)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

CORPUS_SCOPE_BATCH = "batch_corpus"
CORPUS_SCOPE_CROSS_RUN = "cross_run"
VALID_CORPUS_SCOPES = frozenset({CORPUS_SCOPE_BATCH, CORPUS_SCOPE_CROSS_RUN})

RUN_RECORD_KEYS = frozenset(
    {"run_id", "session_id", "merge_mode", "source_files", "fact_count", "created_at"}
)
FACT_RECORD_KEYS = frozenset({"fact_id", "subject", "source_file", "chunk_id", "run_id"})


@dataclass(frozen=True)
class CorpusRunRecord:
    run_id: str
    session_id: str
    merge_mode: str
    source_files: tuple[str, ...]
    fact_count: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "merge_mode": self.merge_mode,
            "source_files": list(self.source_files),
            "fact_count": self.fact_count,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class CorpusFactRecord:
    fact_id: str
    subject: str
    source_file: str
    run_id: str
    chunk_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_scope(merge_mode: str) -> None:
    if merge_mode not in VALID_CORPUS_SCOPES:
        raise ValueError(f"invalid corpus scope: {merge_mode}")


def validate_run_record(data: dict[str, Any]) -> CorpusRunRecord:
    missing = RUN_RECORD_KEYS - set(data)
    if missing:
        raise ValueError(f"corpus run missing keys: {sorted(missing)}")
    validate_scope(str(data["merge_mode"]))
    source_files = data["source_files"]
    if not isinstance(source_files, list) or not source_files:
        raise ValueError("source_files must be non-empty list")
    fact_count = int(data["fact_count"])
    if fact_count < 0:
        raise ValueError("fact_count must be >= 0")
    return CorpusRunRecord(
        run_id=str(data["run_id"]).strip(),
        session_id=str(data["session_id"]).strip(),
        merge_mode=str(data["merge_mode"]),
        source_files=tuple(str(s) for s in source_files),
        fact_count=fact_count,
        created_at=str(data["created_at"]),
    )


def validate_fact_record(data: dict[str, Any]) -> CorpusFactRecord:
    missing = FACT_RECORD_KEYS - set(data)
    if missing:
        raise ValueError(f"corpus fact missing keys: {sorted(missing)}")
    subject = str(data["subject"]).strip()
    source_file = str(data["source_file"]).strip()
    if not subject:
        raise ValueError("subject required")
    if not source_file:
        raise ValueError("source_file required")
    return CorpusFactRecord(
        fact_id=str(data["fact_id"]).strip(),
        subject=subject,
        source_file=source_file,
        run_id=str(data["run_id"]).strip(),
        chunk_id=str(data.get("chunk_id") or ""),
    )


def facts_from_run_dict(
    run_id: str,
    facts: list[dict[str, Any]],
) -> list[CorpusFactRecord]:
    out: list[CorpusFactRecord] = []
    for raw in facts:
        item = dict(raw)
        item.setdefault("run_id", run_id)
        out.append(validate_fact_record(item))
    return out
