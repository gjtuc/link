"""
μ-2b-03-00 — In-memory CorpusStore adapter.

스펙: docs/design/STAGE-1-PERSIST-spec.md
"""

from __future__ import annotations

from deconstructor.corpus.contract import CorpusFactRecord, CorpusRunRecord
from deconstructor.corpus.memory_store import InMemoryCorpusStore


class MemoryCorpusStoreAdapter:
    """Wraps ``InMemoryCorpusStore`` for ``CorpusStore`` protocol."""

    def __init__(self, inner: InMemoryCorpusStore | None = None) -> None:
        self._inner = inner if inner is not None else InMemoryCorpusStore()

    @property
    def inner(self) -> InMemoryCorpusStore:
        return self._inner

    def append_run(
        self,
        run: CorpusRunRecord | dict,
        facts: list[CorpusFactRecord | dict],
    ) -> None:
        self._inner.append_run(run, facts)

    def list_runs(self) -> list[CorpusRunRecord]:
        return self._inner.list_runs()

    def facts_for_run(self, run_id: str) -> list[CorpusFactRecord]:
        return self._inner.facts_for_run(run_id)

    def facts_cross_run(self) -> list[CorpusFactRecord]:
        return self._inner.facts_cross_run()

    def clear(self) -> None:
        self._inner.clear()

    def run_count(self) -> int:
        return self._inner.run_count()

    def fact_count(self) -> int:
        return self._inner.fact_count()

    def distinct_source_files(self) -> list[str]:
        return self._inner.distinct_source_files()
