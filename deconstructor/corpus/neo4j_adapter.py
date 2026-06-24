"""
μ-2b-03-01 — Neo4j CorpusStore adapter (bolt, mockable).

스펙: docs/design/STAGE-1-PERSIST-spec.md
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from deconstructor.corpus.contract import (
    CorpusFactRecord,
    CorpusRunRecord,
    validate_fact_record,
    validate_run_record,
)

SessionFactory = Callable[[], Any]


class _Neo4jSession(Protocol):
    def run(self, query: str, **parameters: Any) -> Any: ...


# --- Cypher (PERSIST spec sketch) ---

CYPHER_ENSURE_SCHEMA = """
CREATE CONSTRAINT corpus_run_id IF NOT EXISTS
FOR (r:CorpusRun) REQUIRE r.run_id IS UNIQUE
"""

CYPHER_ENSURE_FACT_SCHEMA = """
CREATE CONSTRAINT corpus_fact_id IF NOT EXISTS
FOR (f:CorpusFactRef) REQUIRE f.fact_id IS UNIQUE
"""

CYPHER_RUN_EXISTS = """
MATCH (r:CorpusRun {run_id: $run_id})
RETURN r LIMIT 1
"""

CYPHER_CREATE_RUN = """
CREATE (r:CorpusRun {
    run_id: $run_id,
    session_id: $session_id,
    merge_mode: $merge_mode,
    source_files: $source_files,
    fact_count: $fact_count,
    created_at: $created_at
})
"""

CYPHER_LINK_FACT = """
MATCH (r:CorpusRun {run_id: $run_id})
MERGE (f:CorpusFactRef {fact_id: $fact_id})
SET f.subject = $subject,
    f.source_file = $source_file,
    f.chunk_id = $chunk_id,
    f.run_id = $run_id
MERGE (r)-[:CORPUS_MEMBER]->(f)
"""

CYPHER_LIST_RUNS = """
MATCH (r:CorpusRun)
RETURN r
ORDER BY r.created_at, r.run_id
"""

CYPHER_FACTS_CROSS_RUN = """
MATCH (f:CorpusFactRef)
RETURN f
ORDER BY f.run_id, f.fact_id
"""

CYPHER_FACTS_FOR_RUN = """
MATCH (f:CorpusFactRef {run_id: $run_id})
RETURN f
ORDER BY f.fact_id
"""

CYPHER_CLEAR = """
MATCH (n)
WHERE n:CorpusRun OR n:CorpusFactRef
DETACH DELETE n
"""


def _record_to_run(node: dict[str, Any]) -> CorpusRunRecord:
    source_files = node.get("source_files") or []
    if isinstance(source_files, tuple):
        source_files = list(source_files)
    return validate_run_record(
        {
            "run_id": node["run_id"],
            "session_id": node["session_id"],
            "merge_mode": node["merge_mode"],
            "source_files": list(source_files),
            "fact_count": int(node["fact_count"]),
            "created_at": node["created_at"],
        }
    )


def _record_to_fact(node: dict[str, Any]) -> CorpusFactRecord:
    return validate_fact_record(
        {
            "fact_id": node["fact_id"],
            "subject": node["subject"],
            "source_file": node["source_file"],
            "run_id": node["run_id"],
            "chunk_id": node.get("chunk_id") or "",
        }
    )


class Neo4jCorpusStoreAdapter:
    """Persist cross-run corpus refs in Neo4j (:CorpusRun / :CorpusFactRef)."""

    def __init__(
        self,
        *,
        driver: Any | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._driver = driver
        if session_factory is not None:
            self._session_factory = session_factory
        elif driver is not None:
            self._session_factory = driver.session
        else:
            self._session_factory = self._build_default_session_factory()
        self._schema_ready = False

    def _build_default_session_factory(self) -> SessionFactory:
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise ConnectionError(
                "LINK_CORPUS_BACKEND=neo4j requires the neo4j Python driver "
                "(pip install neo4j)."
            ) from exc

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")

        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
        except Exception as exc:
            raise ConnectionError(
                f"LINK_CORPUS_BACKEND=neo4j but bolt connection failed ({exc}). "
                "Check NEO4J_URI / NEO4J_PASSWORD or set LINK_CORPUS_BACKEND=memory."
            ) from exc
        return self._driver.session

    @contextmanager
    def _session(self) -> Iterator[_Neo4jSession]:
        factory = self._session_factory
        ctx = factory()
        if hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__"):
            with ctx as session:
                yield session
            return
        try:
            yield ctx
        finally:
            close = getattr(ctx, "close", None)
            if callable(close):
                close()

    def _ensure_schema(self, session: _Neo4jSession) -> None:
        if self._schema_ready:
            return
        session.run(CYPHER_ENSURE_SCHEMA)
        session.run(CYPHER_ENSURE_FACT_SCHEMA)
        self._schema_ready = True

    def append_run(
        self,
        run: CorpusRunRecord | dict,
        facts: list[CorpusFactRecord | dict],
    ) -> None:
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

        with self._session() as session:
            self._ensure_schema(session)
            existing = session.run(CYPHER_RUN_EXISTS, run_id=run_rec.run_id).single()
            if existing is not None:
                raise ValueError(f"corpus run already exists: {run_rec.run_id!r}")
            session.run(
                CYPHER_CREATE_RUN,
                run_id=run_rec.run_id,
                session_id=run_rec.session_id,
                merge_mode=run_rec.merge_mode,
                source_files=list(run_rec.source_files),
                fact_count=run_rec.fact_count,
                created_at=run_rec.created_at,
            )
            for fact in fact_recs:
                session.run(
                    CYPHER_LINK_FACT,
                    run_id=fact.run_id,
                    fact_id=fact.fact_id,
                    subject=fact.subject,
                    source_file=fact.source_file,
                    chunk_id=fact.chunk_id,
                )

    def list_runs(self) -> list[CorpusRunRecord]:
        with self._session() as session:
            result = session.run(CYPHER_LIST_RUNS)
            runs: list[CorpusRunRecord] = []
            for record in result:
                node = _node_props(record, "r")
                runs.append(_record_to_run(node))
            return runs

    def facts_for_run(self, run_id: str) -> list[CorpusFactRecord]:
        rid = str(run_id).strip()
        if not rid:
            raise ValueError("run_id required")
        with self._session() as session:
            result = session.run(CYPHER_FACTS_FOR_RUN, run_id=rid)
            return [_record_to_fact(_node_props(record, "f")) for record in result]

    def facts_cross_run(self) -> list[CorpusFactRecord]:
        with self._session() as session:
            result = session.run(CYPHER_FACTS_CROSS_RUN)
            return [_record_to_fact(_node_props(record, "f")) for record in result]

    def clear(self) -> None:
        with self._session() as session:
            session.run(CYPHER_CLEAR)

    def run_count(self) -> int:
        return len(self.list_runs())

    def fact_count(self) -> int:
        return len(self.facts_cross_run())

    def distinct_source_files(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for fact in self.facts_cross_run():
            if fact.source_file not in seen:
                seen.add(fact.source_file)
                out.append(fact.source_file)
        return out

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None


def _node_props(record: Any, key: str) -> dict[str, Any]:
    value = record[key]
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "items"):
        return dict(value.items())
    if hasattr(value, "_properties"):
        return dict(value._properties)
    raise TypeError(f"unexpected neo4j node type: {type(value)!r}")
