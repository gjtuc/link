"""μ-2b-03-01 — Neo4j CorpusStore adapter (mock bolt, offline)."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest

from deconstructor.corpus.contract import CORPUS_SCOPE_CROSS_RUN, CorpusFactRecord, CorpusRunRecord
from deconstructor.corpus.factory import clear_corpus_store_singleton, get_corpus_store
from deconstructor.corpus.neo4j_adapter import (
    CYPHER_CLEAR,
    CYPHER_CREATE_RUN,
    CYPHER_FACTS_CROSS_RUN,
    CYPHER_FACTS_FOR_RUN,
    CYPHER_LINK_FACT,
    CYPHER_LIST_RUNS,
    CYPHER_RUN_EXISTS,
    Neo4jCorpusStoreAdapter,
)
from deconstructor.corpus.query import query_facts, summarize_corpus


@dataclass
class _MockResult:
    rows: list[dict[str, Any]] = field(default_factory=list)
    _index: int = 0

    def __iter__(self):
        return iter(self.rows)

    def single(self):
        if not self.rows:
            return None
        return self.rows[0]


@dataclass
class MockCorpusBoltGraph:
    """In-process bolt stand-in for offline pytest."""

    runs: dict[str, dict[str, Any]] = field(default_factory=dict)
    facts: dict[str, dict[str, Any]] = field(default_factory=dict)
    members: set[tuple[str, str]] = field(default_factory=set)

    def clear(self) -> None:
        self.runs.clear()
        self.facts.clear()
        self.members.clear()

    def run(self, query: str, **params: Any) -> _MockResult:
        q = " ".join(query.split())
        if q == CYPHER_RUN_EXISTS.strip().replace("\n", " "):
            run_id = params["run_id"]
            if run_id in self.runs:
                return _MockResult([{"r": dict(self.runs[run_id])}])
            return _MockResult([])
        if q.startswith("CREATE (r:CorpusRun"):
            run_id = params["run_id"]
            self.runs[run_id] = {
                "run_id": run_id,
                "session_id": params["session_id"],
                "merge_mode": params["merge_mode"],
                "source_files": list(params["source_files"]),
                "fact_count": params["fact_count"],
                "created_at": params["created_at"],
            }
            return _MockResult([])
        if "MERGE (f:CorpusFactRef" in q:
            fact_id = params["fact_id"]
            run_id = params["run_id"]
            self.facts[fact_id] = {
                "fact_id": fact_id,
                "subject": params["subject"],
                "source_file": params["source_file"],
                "chunk_id": params.get("chunk_id") or "",
                "run_id": run_id,
            }
            self.members.add((run_id, fact_id))
            return _MockResult([])
        if q.startswith("MATCH (r:CorpusRun) RETURN r"):
            rows = [{"r": dict(v)} for v in sorted(self.runs.values(), key=lambda x: (x["created_at"], x["run_id"]))]
            return _MockResult(rows)
        if q.startswith("MATCH (f:CorpusFactRef) RETURN f"):
            rows = [
                {"f": dict(v)}
                for v in sorted(self.facts.values(), key=lambda x: (x["run_id"], x["fact_id"]))
            ]
            return _MockResult(rows)
        if q.startswith("MATCH (f:CorpusFactRef {run_id:"):
            run_id = params["run_id"]
            rows = [
                {"f": dict(v)}
                for v in sorted(self.facts.values(), key=lambda x: x["fact_id"])
                if v["run_id"] == run_id
            ]
            return _MockResult(rows)
        if "DETACH DELETE n" in q:
            self.clear()
            return _MockResult([])
        if "CREATE CONSTRAINT" in q:
            return _MockResult([])
        raise AssertionError(f"unexpected cypher in mock bolt: {query!r}")

    @contextmanager
    def session(self):
        yield self


def _run_record(run_id: str, session_id: str, source_files: tuple[str, ...], fact_count: int) -> CorpusRunRecord:
    return CorpusRunRecord(
        run_id=run_id,
        session_id=session_id,
        merge_mode=CORPUS_SCOPE_CROSS_RUN,
        source_files=source_files,
        fact_count=fact_count,
        created_at="2026-06-20T00:00:00+00:00",
    )


def _fact(run_id: str, fact_id: str, subject: str, source_file: str) -> CorpusFactRecord:
    return CorpusFactRecord(
        fact_id=fact_id,
        subject=subject,
        source_file=source_file,
        run_id=run_id,
        chunk_id=f"{source_file}#chunk-1/1",
    )


@pytest.fixture
def bolt_graph() -> MockCorpusBoltGraph:
    graph = MockCorpusBoltGraph()
    yield graph
    graph.clear()


@pytest.fixture
def neo4j_store(bolt_graph: MockCorpusBoltGraph) -> Neo4jCorpusStoreAdapter:
    return Neo4jCorpusStoreAdapter(session_factory=bolt_graph.session)


def test_append_two_runs_list_and_cross_run_facts(neo4j_store: Neo4jCorpusStoreAdapter):
    neo4j_store.append_run(
        _run_record("run-n1", "sess-neo", ("a.txt",), 1),
        [_fact("run-n1", "f-a", "Ni catalyst", "a.txt")],
    )
    neo4j_store.append_run(
        _run_record("run-n2", "sess-neo", ("b.txt",), 1),
        [_fact("run-n2", "f-b", "CH4", "b.txt")],
    )
    runs = neo4j_store.list_runs()
    assert [r.run_id for r in runs] == ["run-n1", "run-n2"]
    facts = neo4j_store.facts_cross_run()
    assert {f.fact_id for f in facts} == {"f-a", "f-b"}
    assert neo4j_store.facts_for_run("run-n1")[0].subject == "Ni catalyst"


def test_summarize_corpus_via_query_layer(neo4j_store: Neo4jCorpusStoreAdapter):
    neo4j_store.append_run(
        _run_record("run-n1", "sess-q", ("a.txt",), 1),
        [_fact("run-n1", "f-a", "Ni", "a.txt")],
    )
    neo4j_store.append_run(
        _run_record("run-n2", "sess-q", ("b.txt",), 1),
        [_fact("run-n2", "f-b", "CH4", "b.txt")],
    )
    summary = summarize_corpus(neo4j_store, session_id="sess-q")
    assert summary.run_count == 2
    assert summary.fact_count == 2
    assert set(summary.source_files) == {"a.txt", "b.txt"}


def test_duplicate_run_id_raises_value_error(neo4j_store: Neo4jCorpusStoreAdapter):
    run = _run_record("run-dup", "sess-d", ("x.txt",), 1)
    facts = [_fact("run-dup", "f-x", "topic", "x.txt")]
    neo4j_store.append_run(run, facts)
    with pytest.raises(ValueError, match="corpus run already exists"):
        neo4j_store.append_run(run, facts)


def test_restart_loads_persisted_mock_bolt(bolt_graph: MockCorpusBoltGraph):
    first = Neo4jCorpusStoreAdapter(session_factory=bolt_graph.session)
    first.append_run(
        _run_record("run-rs", "sess-rs", ("p.txt",), 1),
        [_fact("run-rs", "f-p", "persist", "p.txt")],
    )
    restarted = Neo4jCorpusStoreAdapter(session_factory=bolt_graph.session)
    assert restarted.run_count() == 1
    assert restarted.fact_count() == 1
    assert query_facts(restarted, session_id="sess-rs")[0].subject == "persist"


def test_clear_wipes_mock_graph(neo4j_store: Neo4jCorpusStoreAdapter):
    neo4j_store.append_run(
        _run_record("run-c", "sess-c", ("z.txt",), 1),
        [_fact("run-c", "f-z", "z", "z.txt")],
    )
    neo4j_store.clear()
    assert neo4j_store.list_runs() == []
    assert neo4j_store.facts_cross_run() == []


def test_factory_neo4j_branch_uses_adapter(monkeypatch, bolt_graph: MockCorpusBoltGraph):
    monkeypatch.setenv("LINK_CORPUS_BACKEND", "neo4j")
    clear_corpus_store_singleton()

    import deconstructor.corpus.factory as factory_mod

    original = factory_mod._create_store

    def _patched_create(backend: str):
        if backend == "neo4j":
            return Neo4jCorpusStoreAdapter(session_factory=bolt_graph.session)
        return original(backend)

    monkeypatch.setattr(factory_mod, "_create_store", _patched_create)
    store = get_corpus_store()
    assert isinstance(store, Neo4jCorpusStoreAdapter)
    store.append_run(
        _run_record("run-f", "sess-f", ("f.txt",), 1),
        [_fact("run-f", "f-f", "factory", "f.txt")],
    )
    assert store.run_count() == 1
