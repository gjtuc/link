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

__all__ = [
    "CORPUS_SCOPE_BATCH",
    "CORPUS_SCOPE_CROSS_RUN",
    "CorpusFactRecord",
    "CorpusRunRecord",
    "FACT_RECORD_KEYS",
    "RUN_RECORD_KEYS",
    "InMemoryCorpusStore",
    "facts_from_run_dict",
    "utc_now_iso",
    "validate_fact_record",
    "validate_run_record",
    "validate_scope",
]
