"""ABSTAIN / PASS / FAIL aggregator truth table tests."""

from __future__ import annotations

from deconstructor.skeptic.truth_table import (
    build_abstain_combination_table,
    build_core_truth_table,
    verify_truth_table,
)


def test_core_truth_table_all_pass():
    errors = verify_truth_table(build_core_truth_table())
    assert errors == []


def test_abstain_combination_table_all_pass():
    rows = build_abstain_combination_table()
    assert len(rows) == 8  # 2^3 PASS/ABSTAIN combos
    errors = verify_truth_table(rows)
    assert errors == []


def test_unanimous_pass_patterns_accept():
    rows = [r for r in build_abstain_combination_table() if r.expected_step == "A5"]
    assert len(rows) == 7
    assert all(r.expected_accepted for r in rows)


def test_all_abstain_rejects_a4():
    rows = [r for r in build_abstain_combination_table() if r.pattern == "AAA"]
    assert len(rows) == 1
    assert rows[0].expected_step == "A4"
    assert not rows[0].expected_accepted
