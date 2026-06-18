"""Shared expectations for pipeline smoke tests."""

EXPECTED_NODE_SEQUENCE = (
    "deconstruct",
    "verify",
    "deconstruct",
    "verify",
    "skeptic",
    "weaver",
)

EXPECTED_DEPTH_CAP_SEQUENCE = EXPECTED_NODE_SEQUENCE
