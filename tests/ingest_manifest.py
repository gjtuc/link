"""Ingest touch manifest — edit triggers Branch-0 gate (phase_r_regression.py)."""

from __future__ import annotations

# ingest / Phase R core (μ-R implementation)
INGEST_TOUCH_PATHS: tuple[str, ...] = (
    "deconstructor/web/extract.py",
    "deconstructor/web/document_chunks.py",
    "deconstructor/web/ingest_verify.py",
    "deconstructor/guards/ingest_guard.py",
    "deconstructor/provenance/source_meta.py",
    "deconstructor/web/pipeline_batch.py",
    "scripts/ingest_read_verify.py",
    "scripts/phase_r_regression.py",
    "scripts/e2e_common.py",
)

# Branch-2+ spec files must not exist while locked
FORBIDDEN_BRANCH2_GLOBS: tuple[str, ...] = (
    "BRANCH-2b*.md",
    "BRANCH-3*.md",
    "STAGE-1*.md",
)

BRANCH_STATE_PATH = "tests/fixtures/branch_state.json"
