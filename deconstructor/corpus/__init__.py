"""μ-2b-00 — STAGE-1 cross-run corpus contract."""

from deconstructor.corpus.contract import (
    CORPUS_SCOPE_BATCH,
    CORPUS_SCOPE_CROSS_RUN,
    CorpusFactRecord,
    CorpusRunRecord,
    FACT_RECORD_KEYS,
    RUN_RECORD_KEYS,
    facts_from_run_dict,
    utc_now_iso,
    validate_fact_record,
    validate_run_record,
    validate_scope,
)
from deconstructor.corpus.memory_store import InMemoryCorpusStore
from deconstructor.corpus.factory import (
    corpus_backend,
    get_corpus_store,
    reset_corpus_store,
)
from deconstructor.corpus.memory_adapter import MemoryCorpusStoreAdapter
from deconstructor.corpus.store_protocol import CorpusStore
from deconstructor.corpus.ingest_hook import (
    append_pipeline_to_corpus,
    cross_run_corpus_enabled,
    maybe_append_batch_corpus,
)

from deconstructor.corpus.query import (
    CorpusQuerySummary,
    query_facts,
    query_runs,
    summarize_corpus,
)
from deconstructor.corpus.status_block import build_corpus_status_block

__all__ = [
    "CORPUS_SCOPE_BATCH",
    "CORPUS_SCOPE_CROSS_RUN",
    "CorpusFactRecord",
    "CorpusRunRecord",
    "FACT_RECORD_KEYS",
    "RUN_RECORD_KEYS",
    "InMemoryCorpusStore",
    "CorpusStore",
    "MemoryCorpusStoreAdapter",
    "corpus_backend",
    "append_pipeline_to_corpus",
    "cross_run_corpus_enabled",
    "get_corpus_store",
    "maybe_append_batch_corpus",
    "reset_corpus_store",
    "CorpusQuerySummary",
    "query_facts",
    "query_runs",
    "summarize_corpus",
    "build_corpus_status_block",
    "facts_from_run_dict",
    "utc_now_iso",
    "validate_fact_record",
    "validate_run_record",
    "validate_scope",
]
