"""
μ-2b-00 — In-memory cross-run corpus store (skeleton).

스펙: docs/design/STAGE-1-CORPUS-spec.md
선행: contract.py
다음: μ-2b-01 pipeline·Neo4j 경계
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deconstructor.corpus.contract import CorpusFactRecord, CorpusRunRecord, validate_fact_record, validate_run_record


@dataclass
class InMemoryCorpusStore:
    """Process-local STAGE-1 corpus pool — no Neo4j/disk."""

    _runs: list[CorpusRunRecord] = field(default_factory=list)
    _facts: list[CorpusFactRecord] = field(default_factory=list)

    def append_run(self, run: CorpusRunRecord | dict, facts: list[CorpusFactRecord | dict]) -> None:
        run_rec = validate_run_record(run.to_dict() if isinstance(run, CorpusRunRecord) else run)
        fact_recs = [
            f if isinstance(f, CorpusFactRecord) else validate_fact_record(f)
            for f in facts
        ]
        for f in fact_recs:
            if f.run_id != run_rec.run_id:
                raise ValueError(f"fact run_id {f.run_id!r} != run {run_rec.run_id!r}")
        if run_rec.fact_count != len(fact_recs):
            raise ValueError(f"fact_count {run_rec.fact_count} != len(facts) {len(fact_recs)}")
        self._runs.append(run_rec)
        self._facts.extend(fact_recs)

    def list_runs(self) -> list[CorpusRunRecord]:
        return list(self._runs)

    def facts_for_run(self, run_id: str) -> list[CorpusFactRecord]:
        return [f for f in self._facts if f.run_id == run_id]

    def facts_cross_run(self) -> list[CorpusFactRecord]:
        return list(self._facts)

    def distinct_source_files(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for f in self._facts:
            if f.source_file not in seen:
                seen.add(f.source_file)
                out.append(f.source_file)
        return out

    def run_count(self) -> int:
        return len(self._runs)

    def fact_count(self) -> int:
        return len(self._facts)

    def clear(self) -> None:
        self._runs.clear()
        self._facts.clear()
