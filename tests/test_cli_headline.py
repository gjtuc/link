"""Tests for CLI headline resolution."""

from __future__ import annotations

import argparse

from deconstructor.cli.headline import LIVE_DEFAULT_HEADLINE, resolve_headline
from deconstructor.dry_run.scenarios import DEFAULT_HEADLINE, DEPTH_CAP_SCENARIO


def _args(**kw) -> argparse.Namespace:
    return argparse.Namespace(
        event=kw.get("event"),
        depth_cap=kw.get("depth_cap", False),
        dry_run=kw.get("dry_run", False),
        json=False,
        db=False,
        skeptic_only=False,
    )


def test_dry_run_default_headline():
    h, cap = resolve_headline(_args(), dry_run=True)
    assert h == DEFAULT_HEADLINE
    assert cap is None


def test_depth_cap_headline_and_cap():
    h, cap = resolve_headline(_args(depth_cap=True), dry_run=True)
    assert h == DEPTH_CAP_SCENARIO.headline
    assert cap == DEPTH_CAP_SCENARIO.max_recursion_depth


def test_live_default_headline():
    h, cap = resolve_headline(_args(), dry_run=False)
    assert h == LIVE_DEFAULT_HEADLINE
    assert cap is None
