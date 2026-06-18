"""Tests for SkepticEngine aggregation and batch evaluation."""

from deconstructor.skeptic import SkepticEngine
from deconstructor.skeptic.schemas import CausalClassification
from tests.conftest import GRID_OFF, MOTOR_STOP, WEATHER_HOT


class TestSkepticEngine:
    def test_accepts_plausible_causal_chain(self):
        batch = SkepticEngine().evaluate_batch([GRID_OFF, MOTOR_STOP])
        accepted = {
            (e.source_fact_id, e.target_fact_id) for e in batch.verified_edges
        }
        assert ("f1", "f2") in accepted
        assert batch.verified_edges[0].probability > 0
        assert batch.verified_edges[0].latency == 120_000

    def test_rejects_spurious_weather_link(self):
        batch = SkepticEngine().evaluate_batch([GRID_OFF, WEATHER_HOT])
        accepted = {
            (e.source_fact_id, e.target_fact_id) for e in batch.verified_edges
        }
        assert ("f1", "f3") not in accepted
        rejected = [
            r
            for r in batch.rejected
            if r.source_fact_id == "f1" and r.target_fact_id == "f3"
        ]
        assert len(rejected) == 1
        assert rejected[0].classification == CausalClassification.CORRELATION
        assert "R09_CROSS_DOMAIN_ISOLATION" in rejected[0].failed_rule_ids or (
            "R06_MECHANISM_PLAUSIBILITY" in rejected[0].failed_rule_ids
        )

    def test_returns_empty_for_single_fact(self):
        batch = SkepticEngine().evaluate_batch([GRID_OFF])
        assert batch.verified_edges == []
        assert batch.rejected == []
        assert batch.verdicts == []

    def test_pair_count_is_n_times_n_minus_one(self):
        facts = [GRID_OFF, MOTOR_STOP, WEATHER_HOT]
        batch = SkepticEngine().evaluate_batch(facts)
        assert len(batch.verdicts) == 6
