"""
μ-2b-03-00 — CorpusStore factory.

μ-ID: μ-2b-03-00
선행: memory_adapter + store_protocol
env: LINK_CORPUS_BACKEND=memory|neo4j (neo4j → μ-2b-03-01)
스펙: docs/design/STAGE-1-PERSIST-spec.md
"""

from __future__ import annotations

import os

from deconstructor.corpus.memory_adapter import MemoryCorpusStoreAdapter
from deconstructor.corpus.memory_store import InMemoryCorpusStore
from deconstructor.corpus.store_protocol import CorpusStore

_ENV_BACKEND = "LINK_CORPUS_BACKEND"
_DEFAULT_BACKEND = "memory"

_global_store: CorpusStore | None = None


def corpus_backend() -> str:
    return os.getenv(_ENV_BACKEND, _DEFAULT_BACKEND).strip().lower() or _DEFAULT_BACKEND


def _create_store(backend: str) -> CorpusStore:
    if backend == "memory":
        return MemoryCorpusStoreAdapter()
    if backend == "neo4j":
        raise NotImplementedError("LINK_CORPUS_BACKEND=neo4j — μ-2b-03-01")
    raise ValueError(f"unknown LINK_CORPUS_BACKEND: {backend!r}")


def get_corpus_store() -> CorpusStore:
    global _global_store
    if _global_store is None:
        _global_store = _create_store(corpus_backend())
    return _global_store


def reset_corpus_store(store: CorpusStore | InMemoryCorpusStore | None = None) -> CorpusStore:
    """Tests: replace process singleton (always fresh memory when ``store`` is None)."""
    global _global_store
    if store is None:
        _global_store = MemoryCorpusStoreAdapter()
    elif isinstance(store, InMemoryCorpusStore):
        _global_store = MemoryCorpusStoreAdapter(store)
    else:
        _global_store = store
    return _global_store


def clear_corpus_store_singleton() -> None:
    """Drop cached store so next ``get_corpus_store`` re-reads env."""
    global _global_store
    _global_store = None
