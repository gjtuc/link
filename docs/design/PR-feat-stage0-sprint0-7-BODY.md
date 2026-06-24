# PR: feat/stage0-sprint0-7

> **Branch:** `feat/stage0-sprint0-7` → `main`  
> **Repo:** https://github.com/gjtuc/link  
> **설계 근거:** [PROCESS.md](PROCESS.md), [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md)

---

## Summary

STAGE 0 **Sprint 0~7** 구현 + **0단계 클로저 E2E** (S0-A/B/C μ 체크리스트).

- **입력·조립·표현** 계약: document ingest, provenance, bridge, skeleton/recompose UI, corpus FC, watch/guards
- **코어 DAG 불변:** Deconstruct → Verify → Dreamer → Fact-Checker → Skeptic → Weaver → Viz
- **63+ pytest**, S0-A/B/C manual E2E scripts, design docs (`STAGE-0-*`, `SPRINT-*`, `STAGE-0-CLOSURE-spec.md`)

---

## Sprint μ 매핑 (Appendix A~I)

### Sprint 0 — G-FC-UI (M0)

| μ | Task | 산출 |
|---|------|------|
| SP0-FC-01 | `/api/status` parse | `fact_checker`, `tavily_disabled` |
| SP0-FC-02 | Badge | stub/corpus/live labels |
| SP0-FC-03 | `#fc-hint` | graph panel hint |
| SP0-TEST-01 | | `test_sprint0_fc_ui.py` |

### Sprint 1 — G-ING-META (M1)

| μ | Task | 산출 |
|---|------|------|
| SP1-META-01~02 | ExtractedSource meta | `source_file`, `chunk_id`, `page_range` |
| SP1-META-03~05 | Pipeline provenance | `pipeline_batch`, `assign.py` |
| SP1-META-06~07 | AtomicFact + Neo4j tooltip | `models.py`, `neo4j_store.py` |
| SP1-TEST-01 | | `test_sprint1_ingest_meta.py` |

### Sprint 2 — G-ORC-* (M2)

| μ | Task | 산출 |
|---|------|------|
| SP2-POL-01~02 | Dedup policy | `state_graph.py` |
| SP2-BRG-01~02 | Bridge edges | `corpus_bridge.py`, BRIDGE viz |
| SP2-UI-01 | | `orchestration.cross_doc_label` |
| SP2-TEST-01 | | `test_sprint2_orchestration.py` |

### Sprint 3 — G-DEC-* (M3)

| μ | Task | 산출 |
|---|------|------|
| SP3-RECUR-01~03 | Non-atomic recur | prompts, `debug_report` |
| SP3-DENS-01~02 | Density hints | `density_hints.py` |
| SP3-TEST-01 | | `test_sprint3_deconstruct_depth.py` |

### Sprint 4 — G-SKP-INDEX + G-UI-SKELETON (M4)

| μ | Task | 산출 |
|---|------|------|
| SP4-IDX-01~03 | Gap/Strong/Weak | `deconstructor/skeleton/` |
| SP4-API-01 | | `GET /api/skeleton` |
| SP4-UI-01~03 | | `#skeleton-panel`, highlight |
| SP4-TEST-01 | | `test_sprint4_skeleton.py` |

### Sprint 5 — G-FC-CORPUS (M5)

| μ | Task | 산출 |
|---|------|------|
| SP5-CFG-01 | | `resolve_fact_checker_mode()` |
| SP5-POOL/MAT/NODE | | `corpus.py`, `fact_checker_node` |
| SP5-API-03 | | corpus badge UI |
| SP5-TEST-01 | | `test_sprint5_corpus_fc.py` |

### Sprint 6 — G-REC-COMPOSE (M6)

| μ | Task | 산출 |
|---|------|------|
| SP6-RPT/NAR/OUT | ε-2~4 | `deconstructor/recompose/` |
| SP6-API-01 | | `GET /api/recompose` |
| SP6-UI-01 | | `#recompose-panel` tabs |
| SP6-TEST-01 | | `test_sprint6_recompose.py` |

### Sprint 7 — G-DEC-WARN + G-ING-GUARD (M-P2)

| μ | Task | 산출 |
|---|------|------|
| SP7-ING-01~02 | F0-A2 guard | `guards/ingest_guard.py` |
| SP7-DEC/SKP-01 | partial_run, NG-2 | `guards/batch_warnings.py` |
| SP7-UI-01~02 | | `#watch-panel`, debug |
| SP7-TEST-01 | | `test_sprint7_watch.py` |

---

## E2E 클로저 (STAGE-0-CLOSURE)

| 시나리오 | 스크립트 | μ prefix |
|----------|----------|----------|
| S0-A PDF | `scripts/s0a_e2e_run.py` | μ-A-* |
| S0-B 텍스트 | `scripts/s0b_e2e_run.py` | μ-B-* |
| S0-C 다중 파일 | `scripts/s0c_e2e_run.py` | μ-C-* |

상세: [STAGE-0-CLOSURE-spec.md](docs/design/STAGE-0-CLOSURE-spec.md)

---

## Test plan

- [x] `python -m pytest tests/test_sprint*.py tests/test_stage0_acceptance.py tests/test_document_chunks.py`
- [x] `python scripts/s0a_e2e_run.py` — S0-A PASS
- [x] `python scripts/s0b_e2e_run.py --ingest-only` — μ-B-ING PASS (full pipeline pending LLM quota)
- [x] `python scripts/s0c_e2e_run.py --ingest-only` — μ-C-ING PASS (orchestration pending quota)
- [ ] Manual: Link UI PDF upload → skeleton / recompose / watch panels
- [ ] Manual: `/debug.html` partial_run display

---

## NON-GOALS (본 PR)

- 코어 LangGraph 노드 순서·이름 변경
- Tavily 활성화 / LLM full rewrite
- STAGE 1 (cross-run corpus DB, 밀도 median ≥5 MUST)

---

## 관련 문서

- `docs/design/STAGE-0-1` ~ `0-5`, `SPRINT-1` ~ `7`
- `docs/design/S0-A-E2E-RECORD.md`
- `docs/design/PROCESS.md`
