"""The Dreamer — horizontal hypothesis expansion from source facts."""

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.dreamer.schemas import (
    DreamHypothesis,
    DreamHypothesisBroadList,
    DreamHypothesisList,
    FLASH_HYPOTHESIS_MAX,
    FLASH_HYPOTHESIS_MIN,
    PRO_HYPOTHESIS_MAX,
)
from deconstructor.agents.dreamer.stub import (
    stub_dream_hypotheses,
    stub_flash_breadth,
    stub_pro_compress,
)

__all__ = [
    "DreamHypothesis",
    "DreamHypothesisBroadList",
    "DreamHypothesisList",
    "FLASH_HYPOTHESIS_MAX",
    "FLASH_HYPOTHESIS_MIN",
    "PRO_HYPOTHESIS_MAX",
    "apply_hypotheses",
    "dreamer_node",
    "stub_dream_hypotheses",
    "stub_flash_breadth",
    "stub_pro_compress",
]
