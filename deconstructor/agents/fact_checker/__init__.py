"""The Fact-Checker — Tavily search + LLM verification of Dreamer hypotheses."""

from deconstructor.agents.fact_checker.apply import drop_fact, promote_fact
from deconstructor.agents.fact_checker.node import fact_checker_node
from deconstructor.agents.fact_checker.schemas import DroppedHypothesis, VerificationVerdict
from deconstructor.agents.fact_checker.stub import stub_verify_hypothesis

__all__ = [
    "DroppedHypothesis",
    "VerificationVerdict",
    "drop_fact",
    "fact_checker_node",
    "promote_fact",
    "stub_verify_hypothesis",
]
