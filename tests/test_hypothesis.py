"""Tests for pairwise hypothesis generation."""

from deconstructor.skeptic.hypothesis import generate_pairwise_hypotheses
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT


def test_generates_ordered_pairs():
    hyps = generate_pairwise_hypotheses([GRID_OFF, MOTOR_STOP])
    pairs = {(h.source_fact_id, h.target_fact_id) for h in hyps}
    assert pairs == {("f1", "f2"), ("f2", "f1")}

def test_attaches_mechanisms():
    hyps = generate_pairwise_hypotheses(
        [GRID_OFF, MOTOR_STOP],
        mechanisms={("f1", "f2"): "grid powers motor"},
    )
    forward = next(h for h in hyps if h.source_fact_id == "f1")
    assert forward.proposed_mechanism == "grid powers motor"

def test_empty_for_single_fact():
    assert generate_pairwise_hypotheses([GRID_OFF]) == []

def test_six_hypotheses_for_three_facts():
    assert len(generate_pairwise_hypotheses([GRID_OFF, MOTOR_STOP, WEATHER_HOT])) == 6
