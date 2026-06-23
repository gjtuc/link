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
from deconstructor.corpus.ingest_hook import (
    append_pipeline_to_corpus,
    cross_run_corpus_enabled,
    get_corpus_store,
    maybe_append_batch_corpus,
    reset_corpus_store,
)

__all__ = [
    "CORPUS_SCOPE_BATCH",
    "CORPUS_SCOPE_CROSS_RUN",
    "CorpusFactRecord",
    "CorpusRunRecord",
    "FACT_RECORD_KEYS",
    "RUN_RECORD_KEYS",
    "InMemoryCorpusStore",
    "append_pipeline_to_corpus",
    "cross_run_corpus_enabled",
    "get_corpus_store",
    "maybe_append_batch_corpus",
    "reset_corpus_store",
    "facts_from_run_dict",
    "utc_now_iso",
    "validate_fact_record",
    "validate_run_record",
    "validate_scope",
]
