"""Dreamer 2-stage pipeline — Flash breadth → Pro compress."""

from deconstructor.agents.dreamer.llm_runner import (
    build_flash_breadth_messages,
    build_pro_compress_messages,
    format_candidates_block,
)
from deconstructor.agents.dreamer.node import dreamer_node
from deconstructor.agents.dreamer.schemas import (
    FLASH_HYPOTHESIS_MIN,
    PRO_HYPOTHESIS_MAX,
)
from deconstructor.agents.dreamer.stub import stub_flash_breadth, stub_pro_compress
from deconstructor.pipeline.state_factory import make_initial_state
from tests.test_dreamer_stub import _factory_blackout_source


def test_stub_flash_returns_at_least_fifteen_candidates():
    source = _factory_blackout_source()
    broad = stub_flash_breadth([source], raw_text="A공장 정전")
    assert len(broad.hypotheses) >= FLASH_HYPOTHESIS_MIN


def test_stub_pro_compress_reduces_to_three_finalists():
    source = _factory_blackout_source()
    broad = stub_flash_breadth([source], raw_text="A공장 정전")
    assert len(broad.hypotheses) >= FLASH_HYPOTHESIS_MIN
    compressed = stub_pro_compress([source], broad, raw_text="A공장 정전")
    assert 1 <= len(compressed.hypotheses) <= PRO_HYPOTHESIS_MAX
    assert len(compressed.hypotheses) == 3


def test_dreamer_node_logs_flash_and_pro_counts(capsys):
    state = make_initial_state("A공장 정전")
    state["completed_facts"] = [_factory_blackout_source()]
    out = dreamer_node(state, dry_run=True)
    assert len(out["inferred_facts"]) == 3
    log_text = "\n".join(out["dreamer_log"])
    assert "flash breadth=" in log_text
    assert "pro finalists=" in log_text
    captured = capsys.readouterr().out
    assert "[DREAM-S2-4]" in captured


def test_message_builders_include_candidates_block():
    source = _factory_blackout_source()
    broad = stub_flash_breadth([source], raw_text="test")
    flash_msgs = build_flash_breadth_messages([source], headline="headline")
    pro_msgs = build_pro_compress_messages(
        [source], broad.hypotheses, headline="headline"
    )
    assert len(flash_msgs) == 2
    assert len(pro_msgs) == 2
    candidates = format_candidates_block(broad.hypotheses)
    assert "source_fact_id=" in candidates
    assert broad.hypotheses[0].subject in pro_msgs[1].content
