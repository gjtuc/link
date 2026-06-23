"""
μ-2b-02-API — cross-run corpus block for GET /api/status.

μ-ID: μ-2b-02-API
선행: μ-2b-02-R query + μ-2b-01 ingest
스펙: docs/design/STAGE-1-CORPUS-spec.md § API status
"""

from __future__ import annotations

import os

from deconstructor.corpus.ingest_hook import cross_run_corpus_enabled, get_corpus_store
from deconstructor.corpus.query import summarize_corpus

_ENV_SESSION_ID = "LINK_SESSION_ID"


def _disabled_block() -> dict:
    return {
        "enabled": False,
        "run_count": 0,
        "fact_count": 0,
        "source_files": [],
        "session_id": None,
    }


def build_corpus_status_block(*, session_id: str | None = None) -> dict:
    """
    Status payload for ``cross_run_corpus`` (read-only).

    When ``LINK_CROSS_RUN_CORPUS`` is off → fixed disabled shape.
    When on → ``summarize_corpus`` on process store; optional ``LINK_SESSION_ID`` filter.
    """
    if not cross_run_corpus_enabled():
        return _disabled_block()
    sid = session_id
    if sid is None:
        env_sid = os.getenv(_ENV_SESSION_ID, "").strip()
        sid = env_sid or None
    summary = summarize_corpus(get_corpus_store(), session_id=sid)
    return {
        "enabled": True,
        "run_count": summary.run_count,
        "fact_count": summary.fact_count,
        "source_files": list(summary.source_files),
        "session_id": summary.session_id,
    }
