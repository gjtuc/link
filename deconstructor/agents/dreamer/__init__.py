"""The Dreamer — horizontal hypothesis expansion from source facts."""

from deconstructor.agents.dreamer.apply import apply_hypotheses
from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.dreamer.schemas import DreamHypothesis, DreamHypothesisList
from deconstructor.agents.dreamer.stub import stub_dream_hypotheses

__all__ = [
    "DreamHypothesis",
    "DreamHypothesisList",
    "apply_hypotheses",
    "dreamer_node",
    "stub_dream_hypotheses",
]
