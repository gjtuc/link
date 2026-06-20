"""
Sprint 5 — corpus Fact-Checker (SP5-TEST-01).

See ``docs/design/SPRINT-5-corpus-fc-spec.md``.
"""

from __future__ import annotations

from deconstructor import config
from deconstructor.agents.fact_checker.corpus import (
    collect_corpus_pool,
    corpus_verify_hypothesis,
)
from deconstructor.agents.fact_checker.node import fact_checker_node
from deconstructor.models import AtomicFact


def _fact(fid: str, subject: str, state_change: str = "increased", **kw) -> AtomicFact:
    return AtomicFact(
        id=fid,
        subject=subject,
        state_change=state_change,
        is_atomic=True,
        source_type=kw.get("source_type", "extracted"),
        **{k: v for k, v in kw.items() if k != "source_type"},
    )


def _hypothesis(fid: str, subject: str, **kw) -> AtomicFact:
    return AtomicFact(
        id=fid,
        subject=subject,
        state_change=kw.get("state_change", "rose sharply"),
        is_atomic=True,
        source_type="inferred",
        check_status="pending",
        anchor_fact_id=kw.get("anchor_fact_id"),
    )


def test_sp5_cfg02_corpus_mode_when_tavily_disabled(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "key", raising=False)
    monkeypatch.setattr(config, "TAVILY_DISABLED", True)
    monkeypatch.setattr(config, "CORPUS_FC_ENABLED", True)
    assert config.resolve_fact_checker_mode() == "corpus"


def test_sp5_cfg02_stub_when_corpus_disabled(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "", raising=False)
    monkeypatch.setattr(config, "TAVILY_DISABLED", True)
    monkeypatch.setattr(config, "CORPUS_FC_ENABLED", False)
    assert config.resolve_fact_checker_mode() == "stub"


def test_sp5_mat01_exact_subject_promote():
    pool = [_fact("e1", "Ni catalyst", "activity increased")]
    hyp = _hypothesis("h1", "Ni catalyst")
    verdict = corpus_verify_hypothesis(hyp, pool)
    assert verdict.accepted is True
    assert "corpus" in verdict.reason.lower()


def test_sp5_mat04_no_match_drop():
    pool = [_fact("e1", "Solar panel", "efficiency increased")]
    hyp = _hypothesis("h1", "Equity index", state_change="stock price fell")
    verdict = corpus_verify_hypothesis(hyp, pool)
    assert verdict.accepted is False


def test_sp5_mat03_anchor_promote():
    pool = [_fact("e1", "Grid power", "supply dropped")]
    hyp = _hypothesis("h1", "Unknown link", anchor_fact_id="e1")
    verdict = corpus_verify_hypothesis(hyp, pool)
    assert verdict.accepted is True
    assert "anchor" in verdict.reason.lower()


def test_sp5_pool01_collect_extracted_only():
    state = {
        "corpus_fact_pool": [_fact("a", "A", source_type="extracted")],
        "completed_facts": [
            _fact("b", "B", source_type="inferred", check_status="promoted"),
            _fact("c", "C", source_type="extracted"),
        ],
    }
    pool = collect_corpus_pool(state)
    ids = {f.id for f in pool}
    assert ids == {"a", "c"}


def test_sp5_node01_corpus_mode_promotes_on_match():
    pool_fact = _fact("doc1", "Battery voltage", "increased")
    hyp = _hypothesis("inf1", "Battery voltage", state_change="increased")
    state = {
        "inferred_facts": [hyp],
        "completed_facts": [pool_fact],
        "corpus_fact_pool": [],
    }
    out = fact_checker_node(state, mode="corpus")
    assert len(out["promoted_facts"]) == 1
    assert out["promoted_facts"][0].check_status == "promoted"
    assert len(out["dropped_hypotheses"]) == 0


def test_sp5_node01_corpus_mode_drops_without_evidence():
    hyp = _hypothesis("inf1", "Unrelated market index")
    state = {
        "inferred_facts": [hyp],
        "completed_facts": [_fact("doc1", "Battery voltage", "increased")],
        "corpus_fact_pool": [],
    }
    out = fact_checker_node(state, mode="corpus")
    assert len(out["promoted_facts"]) == 0
    assert len(out["dropped_hypotheses"]) == 1


def test_sp5_pool02_batch_pool_from_prior_run():
    prior = _fact("p1", "Ni catalyst", "active")
    hyp = _hypothesis("h1", "Ni catalyst")
    state = {
        "inferred_facts": [hyp],
        "completed_facts": [],
        "corpus_fact_pool": [prior],
    }
    out = fact_checker_node(state, mode="corpus")
    assert len(out["promoted_facts"]) == 1
