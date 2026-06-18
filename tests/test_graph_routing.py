"""Tests for LangGraph routing after verify."""

from deconstructor.routing.after_verify import route_after_verify
from tests.conftest import GRID_OFF, MOTOR_STOP


def _state(**overrides):
    base = {
        "raw_text": "test",
        "extracted_facts": [],
        "completed_facts": [],
        "recursion_depth": 1,
        "max_recursion_depth": 5,
        "partial_run": False,
        "partial_run_reason": "",
        "skeptic_log": [],
        "verified_edges": [],
        "rejected_hypotheses": [],
        "skeptic_verdicts": [],
        "weaver_result": None,
    }
    base.update(overrides)
    return base


class TestRouteAfterVerify:
    def test_routes_to_skeptic_when_all_atomic(self):
        assert route_after_verify(_state()) == "skeptic"

    def test_routes_to_deconstruct_when_non_atomic_remain(self):
        non_atomic = GRID_OFF.model_copy(update={"is_atomic": False})
        state = _state(extracted_facts=[non_atomic], recursion_depth=2)
        assert route_after_verify(state) == "deconstruct"

    def test_routes_to_skeptic_at_depth_cap(self):
        non_atomic = GRID_OFF.model_copy(update={"is_atomic": False})
        state = _state(
            extracted_facts=[non_atomic],
            recursion_depth=5,
            max_recursion_depth=5,
        )
        assert route_after_verify(state) == "skeptic"
