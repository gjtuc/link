"""
μ-2b-03-00 — CorpusStore protocol (adapter contract).

스펙: docs/design/STAGE-1-PERSIST-spec.md
"""

from __future__ import annotations

from typing import Protocol

from deconstructor.corpus.contract import CorpusFactRecord, CorpusRunRecord


class CorpusStore(Protocol):
    """Cross-run corpus storage — same semantics as InMemoryCorpusStore."""

    def append_run(
        self,
        run: CorpusRunRecord | dict,
        facts: list[CorpusFactRecord | dict],
    ) -> None: ...

    def list_runs(self) -> list[CorpusRunRecord]: ...

    def facts_for_run(self, run_id: str) -> list[CorpusFactRecord]: ...

    def facts_cross_run(self) -> list[CorpusFactRecord]: ...

    def clear(self) -> None: ...
