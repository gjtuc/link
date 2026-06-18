"""Tests for extracted_facts trace handler."""

from deconstructor.models import AtomicFact
from deconstructor.pipeline.trace.summarize.handlers.extracted import (
    count_extracted_facts,
    detail_extracted_facts,
)


def test_detail_extracted_facts():
    update = {
        "extracted_facts": [
            AtomicFact(subject="a", state_change="x -> y", is_atomic=False),
            AtomicFact(subject="b", state_change="p -> q", is_atomic=True),
        ]
    }
    assert detail_extracted_facts(update) == "extracted=2 non_atomic=1"
    assert count_extracted_facts(update) == 2


def test_detail_extracted_missing():
    assert detail_extracted_facts({}) is None
    assert count_extracted_facts({}) is None
