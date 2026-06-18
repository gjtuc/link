"""Tests for completed_facts trace handler."""

from deconstructor.models import AtomicFact
from deconstructor.pipeline.trace.summarize.handlers.completed import (
    count_completed_facts,
    detail_completed_facts,
)


def test_detail_completed_facts():
    facts = [AtomicFact(subject="a", state_change="x -> y", is_atomic=True)]
    update = {"completed_facts": facts}
    assert detail_completed_facts(update) == "completed+=1"
    assert count_completed_facts(update) == 1


def test_detail_completed_missing():
    assert detail_completed_facts({}) is None
    assert count_completed_facts({}) is None
