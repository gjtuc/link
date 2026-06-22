"""
Q2 — capabilities card (branch/E2E/ingest → UI human_line).

μ-Q2-02: build_capabilities()
스펙: docs/design/Q2-CAPABILITIES-spec.md
"""

from deconstructor.capabilities.build import (
    CAPABILITY_ITEM_KEYS,
    build_capabilities,
)

__all__ = ["CAPABILITY_ITEM_KEYS", "build_capabilities"]
