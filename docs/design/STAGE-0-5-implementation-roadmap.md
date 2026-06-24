# STAGE 0-5 — 구현 로드맵 (완료본)

> **진행 상태:** 1차 작성 → 재쪼개기(ω) → 점검·수정 → **주석 고정 완료**  
> **입력:** [STAGE-0-4-current-vs-target.md](STAGE-0-4-current-vs-target.md) (G-*, Sprint 순서)  
>         [STAGE-0-3-acceptance-criteria.md](STAGE-0-3-acceptance-criteria.md) (AC-*)  
>         [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) (S0-*)  
> **다음:** **0단계 완료** — Sprint 0~7 ✅ (M0~M6 + M-P2)

---

## 0-5 목적

0-4 G-* 갭을 **실행 가능한 Sprint**로 변환한다.

- **M-* (Milestone):** 구현 단계 1~10과 대응하는 중간 목표  
- **D-* (Dependency):** Sprint·G-* 선행 조건 — 순서 뒤바꿈 방지  
- **SP{n}-* (Sprint task):** 한 Sprint 안의 원자 작업 — 구현·테스트·문서  
- **Sprint DoD:** 완료 시 0-3 AC 표 갱신 + 코드 STAGE 주석 + Appendix 완료본

**코어 파이프라인 변경 금지** (PROCESS.md):  
Deconstruct → Verify → Dreamer → Fact-Checker → Skeptic → Weaver → Viz  
Sprint는 **입력·조립·표현·메타·지표** 만 확장한다.

---

## M-* — 마일스톤 맵

| M-ID | 구현 단계 | Sprint | G-* | AC (주요) | S0 |
|------|-----------|--------|-----|-----------|-----|
| **M0** | UI / C-4 | **Sprint 0** ✅ | G-FC-UI | AC-FC-02 ✅ | A, B |
| **M1** | 1b ingest meta | **Sprint 1** | G-ING-META | AC-ING-05 ❌→✅ | A, C |
| **M2** | 2 corpus | **Sprint 2** | G-ORC-* | AC-ORC-02,03,04 | C |
| **M3** | 3~4 Deconstruct | **Sprint 3** | G-DEC-* | AC-DEC-02,03 | A, B |
| **M4** | 7 + 9 skeleton UI | **Sprint 4** ✅ | G-SKP-INDEX, G-UI-SKELETON | AC-SKP-03,04, UI-04,05 | A, B |
| **M5** | 6 corpus FC | **Sprint 5** ✅ | G-FC-CORPUS | AC-FC-02 full, FC-05 | A |
| **M6** | 10 re-compose | **Sprint 6** ✅ | G-REC-COMPOSE | AC-REC-02 | — |
| **M-P2** | 감시·경고 | **Sprint 7** ✅ | G-DEC-WARN, G-ING-GUARD, G-SKP-05 | AC-DEC-04, ING-07, SKP-05 | A, F |

**M0~M4** = 0-4 백로그 **필수 경로**. M5~M7 = Later (0-5에서 범위만 고정).

---

## D-* — 의존성 그래프

```
                    [Sprint 0: G-FC-UI]  ← 선행 없음 (D-00)
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  │                  │
  [Sprint 1: G-ING-META]    │                  │
         │                  │                  │
         ▼                  │                  │
  [Sprint 2: G-ORC-*] ◄────┘ (D-01: provenance 있으면 bridge 디버깅 용이)
         │
         │ (D-02: 다중 파일과 무관 — Sprint 3은 Sprint 1 후 권장)
         ▼
  [Sprint 3: G-DEC-DENS, G-DEC-RECUR]
         │
         ▼ (D-03: skeleton은 completed graph 필요)
  [Sprint 4: G-SKP-INDEX → G-UI-SKELETON]
         │
         ▼
  [Sprint 5+: corpus FC, re-compose]
```

| D-ID | 규칙 | 이유 |
|------|------|------|
| **D-00** | Sprint 0은 **어떤 Sprint에도 비의존** | UI 라벨만; 파이프라인·스키마 무변경 |
| **D-01** | Sprint 1 **완료 후** Sprint 2 권장 | bridge·dedup 시 fact 출처(C-2) 필요 |
| **D-02** | Sprint 3은 Sprint 1 **후** | DEC 밀도 측정 시 chunk 단위 집계 |
| **D-03** | G-SKP-INDEX **선행** G-UI-SKELETON | UI는 index API 소비만 (7→9) |
| **D-04** | G-DEC-RECUR와 G-DEC-DENS **동 Sprint** | 같은 Verify·Deconstruct 루프; 분리 구현 비효율 |
| **D-05** | G-ORC-POLICY **선행** G-ORC-BRIDGE 알고리즘 | dedup 규칙 없이 merge 확장 시 NG-2 위험 |
| **D-06** | 코어 노드 **삭제·순서 변경 금지** | 모든 Sprint |

---

## Sprint 공통 DoD (Definition of Done)

각 Sprint 완료 시 **반드시**:

1. 본 문서 **Appendix 해당 Sprint** — 완료본 + ω 점검 체크  
2. [STAGE-0-3-acceptance-criteria.md](STAGE-0-3-acceptance-criteria.md) — 해당 AC-* 「상태」 열 갱신  
3. touched 파일 — `STAGE 0-5 / Sprint N` 블록 주석 (또는 기존 STAGE 블록에 Sprint N 완료 표시)  
4. `pytest tests/test_stage0_acceptance.py` — **PASS** (회귀)  
5. (해당 시) Sprint 전용 테스트 파일 추가 — `tests/test_sprint{N}_*.py`  
6. **NON-GOALS** — 해당 Sprint 범위 밖 코드 변경 없음 (범위 creep 기록)

---

## 테스트 전략 (T-*)

| T-ID | 범위 | AC | 실행 |
|------|------|-----|------|
| **T-FAST** | ingest, chunk, NEG | AC-ING, AC-NEG | `test_stage0_acceptance.py` — **매 Sprint** |
| **T-API** | `/api/status`, debug JSON | AC-FC-01, AC-DBG | Sprint 0, 4 |
| **T-UNIT** | skeleton index, merge policy | AC-SKP-03, ORC-03 | Sprint 2, 4 — offline |
| **T-E2E** | PDF fixture, median facts/chunk | AC-DEC-02 (SHOULD) | Sprint 3 — **optional expensive** |
| **T-MANUAL** | S0-A PDF, S0-C multi-file | A0-* | Sprint 0~4 마일스톤마다 1회 |

---

# Appendix A — Sprint 0 (M0: G-FC-UI) ✅

> **완료:** SP0-FC-01~03, SP0-TEST-01, SP0-DOC-01  
> **AC:** AC-FC-02 ⚠️→✅  
> **테스트:** `tests/test_sprint0_fc_ui.py`, `test_stage0_acceptance.py`

### 목표

stub Fact-Checker 모드를 **UI에서 숨기지 않음** (C-4, δ).  
**파이프라인·AtomicFact·Neo4j 변경 없음.**

### 시나리오

| S0 | Step |
|----|------|
| S0-A | A-2-4 stub FC → 「미검증 가설」 |
| S0-B | 동일 |

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-FC-02 | ⚠️ JSON만 | ✅ index UI + `#fc-hint` |

### SP0-* 작업 목록

| Task | 설명 | 파일 |
|------|------|------|
| **SP0-FC-01** | `fetch("/api/status")` → `fact_checker`, `tavily_disabled` 파싱 | `web/index.html` | ✅ |
| **SP0-FC-02** | `updateBackendStatus` 확장: stub → 「미검증 가설」배지; live → 「웹 검색 검증」 | `web/index.html` | ✅ |
| **SP0-FC-03** | 그래프 패널 `#fc-hint` + 완료 status 1줄 힌트 | `web/index.html` | ✅ |
| **SP0-TEST-01** | status mode + index wiring | `tests/test_sprint0_fc_ui.py` | ✅ |
| **SP0-DOC-01** | 0-3 AC-FC-02 ✅, Appendix A 완료본 | design docs | ✅ |

### 합격식 (관측)

- `TAVILY_DISABLED=True` → 헤더 `#backend-status` 텍스트에 **「미검증」** 또는 **「stub」** 동등어 포함  
- `fact_checker: "live"` → 「웹 검색」 또는 동등어  
- AC-FC-01 회귀 — JSON 필드 유지

### NON-GOALS (Sprint 0)

- Tavily 활성화, corpus FC (M5)  
- Deconstruct·Verify 로직 변경  
- Skeleton / Outline UI

---

# Appendix B — Sprint 1 (M1: G-ING-META) ✅

> **완료:** SP1-META-01~08, SP1-TEST-01, SP1-DOC-01  
> **AC:** AC-ING-05 ❌→✅  
> **상세:** [SPRINT-1-ingest-meta-spec.md](SPRINT-1-ingest-meta-spec.md)  
> **테스트:** `tests/test_sprint1_ingest_meta.py`

### 목표

C-2: 각 `AtomicFact`에 **출처 provenance** — `source_file`, `page_range`, `chunk_id` (및 선택 `chunk_label`).

### 시나리오

| S0 | Step |
|----|------|
| S0-A | A-2-1 청크별 fact 추적 |
| S0-C | 다중 파일 시 `source_file` 구분 |

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-ING-05 | ❌ | ✅ |

### SP1-* 작업 목록

| Task | 설명 | 파일 |
|------|------|------|
| **SP1-META-01** | `ExtractedSource` 확장: `source_file`, `chunk_id`, `page_range`, `chunk_index`, `chunk_total` | `web/extract.py` |
| **SP1-META-02** | `document_sources_from_bytes` / `chunk_*` — 메타 채우기 | `web/document_chunks.py`, `extract.py` |
| **SP1-META-03** | `run_pipeline_batch` → `run_pipeline_with_steps`에 provenance dict 전달 | `pipeline_batch.py`, `pipeline_link.py` |
| **SP1-META-04** | `make_initial_state` / State — `source_provenance` (또는 동등) | `pipeline/state_factory.py`, `pipeline/state.py` |
| **SP1-META-05** | Deconstruct 후 fact 생성 시 meta 복사 — `tag_as_extracted` 또는 deconstruct node | `provenance/assign.py`, `deconstruct/node.py` |
| **SP1-META-06** | `AtomicFact` optional fields: `source_file`, `page_range`, `chunk_id` | `models.py` |
| **SP1-META-07** | Neo4j MERGE·pyvis tooltip에 meta 표시 (최소) | `weaver/neo4j_store.py`, `viz/state_graph.py` |
| **SP1-META-08** | debug_report / pipeline_debug — chunk별 fact count | `web/debug_report.py` |
| **SP1-TEST-01** | fixture txt 2 chunks → all facts have chunk_id | `tests/test_sprint1_ingest_meta.py` |
| **SP1-DOC-01** | 0-3 AC-ING-05 ✅ | design docs |

### 합격식

- `pipeline_debug` 또는 `/api/debug/pipeline` — 임의 fact 1건에 `source_file` + `chunk_id` non-null  
- 기존 AC-ING-01~04 **회귀 없음** (T-FAST)

### NON-GOALS (Sprint 1)

- cross-doc bridge (Sprint 2)  
- skeleton index (Sprint 4)  
- fact 밀도 LLM 프롬프트 변경 (Sprint 3)

---

# Appendix C — Sprint 2 (M2: G-ORC-*) ✅

> **완료:** SP2-POL~UI, SP2-TEST-01, SP2-DOC-01  
> **AC:** AC-ORC-02,03,04 ✅  
> **상세:** [SPRINT-2-orchestration-spec.md](SPRINT-2-orchestration-spec.md)  
> **테스트:** `tests/test_sprint2_orchestration.py`

### 목표

S0-C: N 파일 ingest 후 **교차 원인→결과** 또는 **「교차 0건」** 투명 표시. merge-only 한계 명시.

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-ORC-02 | ❌ | ✅ bridge count 또는 UI 「교차 0건」 |
| AC-ORC-03 | ❌ | ✅ 정책 문서 + 코드 주석 |
| AC-ORC-04 | ⚠️ | ✅ UI/API PARTIAL 명시 |

### SP2-* 작업 목록

| Task | 설명 | 파일 |
|------|------|------|
| **SP2-POL-01** | **G-ORC-POLICY** — duplicate `subject` merge 규칙 문서 (0-5 Appendix C-1) | design + `viz/state_graph.py` |
| **SP2-POL-02** | `merge_graph_results` — id 충돌 시 label/source_file 보존 정책 | `viz/state_graph.py` |
| **SP2-BRG-01** | **G-ORC-BRIDGE** — corpus fact pool (배치 내) + subject/state 유사 bridge 후보 | `pipeline_batch.py` (신규 helper) |
| **SP2-BRG-02** | bridge_edges → GraphEdge `edge_type=BRIDGE` (또는 dashed) | `viz/state_graph.py`, `visualizer.py` |
| **SP2-UI-01** | **G-ORC-LABEL** — 결과 JSON `bridge_count`, UI 「교차 N건」/「교차 0건」 | `index.html`, analyze result |
| **SP2-TEST-01** | 2-file fixture — merge + bridge_count ≥0 | `tests/test_sprint2_orchestration.py` |
| **SP2-DOC-01** | F0-C2 한계 vs bridge — STAGE-0-2 F0-C2 갱신 | design docs |

### Appendix C-1 — ORC subject dedup 정책 (초안)

| Case | 정책 |
|------|------|
| 동일 `subject` + 다른 `source_file` | **별도 노드 유지** (Sprint 2); tooltip에 file 표시 |
| 동일 `subject` + 동일 file + 다른 chunk | **별도 노드** (chunk_id 구분) |
| 동일 id UUID 충돌 (merge) | **나중 run wins** (현행); Sprint 2에서 `source_file` tooltip 병합 |

### NON-GOALS (Sprint 2)

- LLM 기반 cross-doc inference  
- 전역 corpus DB (Neo4j cross-run) — **배치 내**만  
- Sprint 3 Deconstruct 변경

---

# Appendix D — Sprint 3 (M3: G-DEC-DENS, G-DEC-RECUR) ✅

> **완료:** SP3-RECUR/DENS, SP3-TEST-01, SP3-DOC-01  
> **AC:** AC-DEC-03 ✅; AC-DEC-02 ⚠️→관측+힌트  
> **상세:** [SPRINT-3-deconstruct-depth-spec.md](SPRINT-3-deconstruct-depth-spec.md)  
> **테스트:** `tests/test_sprint3_deconstruct_depth.py`

### 목표

청크당 fact **밀도** 개선 + Verify **non-atomic 재분해** 실제 발생 (β-2).

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-DEC-02 | ⚠️ ~1/chunk | ⚠️→✅ median ≥5 (SHOULD; 튜닝 가능) |
| AC-DEC-03 | ❌ | ✅ recursion_depth>1 비율 >0 |

### SP3-* 작업 목록

| Task | 설명 | 파일 |
|------|------|------|
| **SP3-RECUR-01** | Deconstruct 프롬프트 — composite fact → `is_atomic=false` 유도 (과도한 true 방지) | `deconstruct/prompts.py` |
| **SP3-RECUR-02** | `partition_by_atomicity` / verify — edge case 점검 | `verify/partition.py` |
| **SP3-RECUR-03** | `recursion_depth` increment 경로 검증 + debug 노출 | `routing/after_verify.py`, `debug_report.py` |
| **SP3-DENS-01** | 청크 길이 대비 min facts 힌트 (프롬프트 또는 post-check warn) | `deconstruct/` |
| **SP3-DENS-02** | `pipeline_debug.counts.completed_facts` **per chunk** (Sprint 1 meta 필요) | `debug_report.py` |
| **SP3-TEST-01** | stub deconstruct fixture — non-atomic → depth 2 | `tests/test_sprint3_verify_recur.py` |
| **SP3-TEST-02** | (optional T-E2E) real PDF median — mark `@pytest.mark.expensive` | `tests/test_sprint3_e2e_density.py` |
| **SP3-DOC-01** | AC-DEC-02 threshold 「SHOULD·튜닝 가능」 유지 | 0-3 |

### NON-GOALS (Sprint 3)

- skeleton Gap/Strong (Sprint 4)  
- 코어 그래프 토폴로지 변경 (dreamer/fc/skeptic 순서)  
- NG-2: node count 목표 아님

---

# Appendix E — Sprint 4 (M4: G-SKP-INDEX + G-UI-SKELETON) ✅

> **완료:** SP4-IDX-01~03, SP4-API-01, SP4-UI-01~03, SP4-TEST-01, SP4-DOC-01  
> **AC:** AC-SKP-03,04,05 · AC-UI-04,05 ✅  
> **상세:** [SPRINT-4-skeleton-ui-spec.md](SPRINT-4-skeleton-ui-spec.md)  
> **테스트:** `tests/test_sprint4_skeleton.py`

### 목표

C-3, NG-4: **skeleton index** (Gap/Strong/Weak) + **Claim tree / Skeleton Health** UI.

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-SKP-03 | ❌ | ✅ Gap count |
| AC-SKP-04 | ❌ | ✅ Strong chain ≥1 (when applicable) |
| AC-SKP-05 | ⚠️ 수동 | ✅ SKP-03/04로 판정 |
| AC-UI-04 | ❌ | ✅ Outline |
| AC-UI-05 | ❌ | ✅ Health panel |

### SP4-* 작업 목록

| Task | 설명 | 파일 | 상태 |
|------|------|------|------|
| **SP4-IDX-01** | **G-SKP-INDEX** — `skeleton_index(graph)` | `deconstructor/skeleton/` | ✅ |
| **SP4-IDX-02** | Gap: in-degree 0 on conclusion-like | `skeleton/rules.py` | ✅ |
| **SP4-IDX-03** | Strong: CAUSES chain length ≥2 | `skeleton/rules.py` | ✅ |
| **SP4-API-01** | `skeleton` block + `GET /api/skeleton` | `pipeline_batch.py`, `server.py` | ✅ |
| **SP4-UI-01** | Outline panel | `web/index.html` | ✅ |
| **SP4-UI-02** | Skeleton Health Gap/Strong/Weak | `web/index.html` | ✅ |
| **SP4-UI-03** | click → graph highlight | `index.html`, `legend.py` | ✅ |
| **SP4-TEST-01** | fixture Gap/Strong counts | `tests/test_sprint4_skeleton.py` | ✅ |
| **SP4-DOC-01** | γ ↔ 코드 1:1 | design docs | ✅ |

### 합격식 (관측)

- analyze JSON — `skeleton.gap_count`, `strong_chain_count`, `outline[]`  
- index.html — `#skeleton-health`, `#skeleton-outline`  
- fixture A→B→C — `strong_chain_count >= 1`

### NON-GOALS (Sprint 4)

- 재조리 텍스트 (M6)  
- corpus FC (M5)  
- force graph 제거 (병행 표시)

---

# Appendix G — Sprint 5 (M5: G-FC-CORPUS) ✅

> **완료:** SP5-CFG-01~02, SP5-POOL-01~03, SP5-MAT-01~04, SP5-NODE-01~02, SP5-API-01~03, SP5-TEST-01  
> **AC:** AC-FC-02 full, AC-FC-05 ✅  
> **상세:** [SPRINT-5-corpus-fc-spec.md](SPRINT-5-corpus-fc-spec.md)  
> **테스트:** `tests/test_sprint5_corpus_fc.py`

### 목표

TAVILY_DISABLED 논문 모드: Dreamer 가설을 **문서 extracted fact corpus**로 promote/drop (Tavily 0 호출).

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-FC-02 | ✅ stub UI only | ✅ corpus → 「문서 내부 검증」 |
| AC-FC-05 | 🔜 | ✅ live → 「웹 검색 검증」 |
| AC-FC-04 | ✅ | ✅ corpus 경로 Tavily 0 유지 |

### SP5-* 작업 목록

| Task | 설명 | 파일 | 상태 |
|------|------|------|------|
| **SP5-CFG-01** | `CORPUS_FC_ENABLED`, `resolve_fact_checker_mode()` | `config.py` | ✅ |
| **SP5-POOL-01** | `collect_corpus_pool`, batch accum | `corpus.py`, `pipeline_batch.py` | ✅ |
| **SP5-MAT-01** | subject/anchor match rules | `corpus.py` | ✅ |
| **SP5-NODE-01** | `fact_checker_node(mode=corpus)` | `node.py`, `builder.py` | ✅ |
| **SP5-API-01** | analyze `fact_checker` block | `pipeline_batch.py` | ✅ |
| **SP5-API-03** | index corpus badge + hint | `index.html` | ✅ |
| **SP5-TEST-01** | unit + node integration | `tests/test_sprint5_corpus_fc.py` | ✅ |

### 합격식

- `TAVILY_DISABLED=True` → `/api/status` `fact_checker: corpus`  
- promoted reasoning contains `corpus:` prefix  
- fixture subject match → promote; unrelated → drop

### NON-GOALS (Sprint 5)

- Tavily 활성화 변경  
- LLM corpus verifier  
- 코어 DAG 순서 변경

---

# Appendix H — Sprint 6 (M6: G-REC-COMPOSE) ✅

> **완료:** SP6-RPT-*, SP6-NAR-*, SP6-OUT-*, SP6-API-*, SP6-UI-*, SP6-TEST-01  
> **AC:** AC-REC-02 ✅  
> **상세:** [SPRINT-6-recompose-spec.md](SPRINT-6-recompose-spec.md)  
> **테스트:** `tests/test_sprint6_recompose.py`

### 목표

**10단계 post-pipeline:** skeleton + graph → ε-2 report, ε-3 verified narrative, ε-4 rewrite outline.

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-REC-02 | 🔜 | ✅ recompose block + UI tabs |
| AC-REC-01 | ✅ | ✅ pipeline inline rewrite 없음 |

### SP6-* 작업 목록

| Task | 설명 | 파일 | 상태 |
|------|------|------|------|
| **SP6-RPT-01** | health report markdown | `recompose/report.py` | ✅ |
| **SP6-NAR-01** | strong chain narrative | `recompose/narrative.py` | ✅ |
| **SP6-OUT-01** | rewrite outline hints | `recompose/outline.py` | ✅ |
| **SP6-API-01** | analyze `recompose` + `/api/recompose` | `pipeline_batch.py`, `server.py` | ✅ |
| **SP6-UI-01** | Report/Narrative/Rewrite tabs | `web/index.html` | ✅ |
| **SP6-TEST-01** | unit + index keys | `tests/test_sprint6_recompose.py` | ✅ |

### 합격식

- analyze JSON — `recompose.report_markdown`, `verified_narrative`, `rewrite_outline[]`  
- fixture A→B→C — `has_strong_narrative: true`  
- index.html — `#recompose-panel` tabs

### NON-GOALS (Sprint 6)

- LLM full rewrite prose  
- 코어 파이프라인 노드 추가

---

# Appendix I — Sprint 7 (M-P2: G-DEC-WARN + G-ING-GUARD + G-SKP-05) ✅

> **완료:** SP7-ING-*, SP7-DEC-*, SP7-SKP-*, SP7-API-*, SP7-UI-*, SP7-TEST-01  
> **AC:** AC-DEC-04, AC-ING-07, AC-SKP-05 ✅  
> **상세:** [SPRINT-7-watch-spec.md](SPRINT-7-watch-spec.md)  
> **테스트:** `tests/test_sprint7_watch.py`

### 목표

P2 **감시·경고:** partial_run 메인 UI, F0-A2 ingest 차단, NG-2 skeleton 힌트.

### AC closure

| AC | Before | After |
|----|--------|-------|
| AC-DEC-04 | ⚠️ debug only | ✅ `#watch-panel` + debug |
| AC-ING-07 | ⚠️ 수동 | ✅ S1-GUARD blocking |
| AC-SKP-05 | ✅ Sprint 4 | ✅ NG-2 watch hint |

### SP7-* 작업 목록

| Task | 설명 | 파일 | 상태 |
|------|------|------|------|
| **SP7-ING-01** | `document_page_count` on PDF | `extract.py` | ✅ |
| **SP7-ING-02** | F0-A2 detect + block | `guards/ingest_guard.py` | ✅ |
| **SP7-DEC-01** | partial_run warnings | `guards/batch_warnings.py` | ✅ |
| **SP7-SKP-01** | NG-2 hint | `guards/batch_warnings.py` | ✅ |
| **SP7-API-01** | analyze `watch` block | `pipeline_batch.py` | ✅ |
| **SP7-UI-01** | `#watch-panel` | `index.html` | ✅ |
| **SP7-UI-02** | debug partial_run display | `debug.html`, `debug_report.py` | ✅ |
| **SP7-TEST-01** | guards unit tests | `tests/test_sprint7_watch.py` | ✅ |

### NON-GOALS (Sprint 7)

- partial_run 자동 복구  
- summarize 모드 제거

---

# Appendix F — Later (reserved)

| Sprint | M-ID | G-* / 주제 | AC | 비고 |
|--------|------|------------|-----|------|
| **7** | M-P2 | G-DEC-WARN, G-ING-GUARD, G-SKP-05 | DEC-04, ING-07, SKP-05 | P2 감시·경고 |

Sprint 7 상세 SP* 목록은 **Sprint 6 완료 후** Appendix F 확장.

---

# ω — 0-5 자기 점검

### ω-1. G-* → Sprint 1:1

| G-* | Sprint |
|-----|--------|
| G-FC-UI | 0 |
| G-ING-META | 1 |
| G-ORC-BRIDGE, POLICY, LABEL | 2 |
| G-DEC-DENS, RECUR | 3 |
| G-SKP-INDEX, G-UI-SKELETON | 4 |
| G-FC-CORPUS | 5 |
| G-REC-COMPOSE | 6 |
| G-DEC-WARN, G-ING-GUARD | 7 |

누락 없음 ✅

### ω-2. D-* 순서 vs 0-4 백로그

0-4 권장 순서(Sprint 0→1→2→3→4)와 **일치** ✅  
Sprint 2 내: POLICY(D-05) → BRIDGE → LABEL 순 ✅

### ω-3. 코어 파이프라인

Sprint 0~2: orchestration·UI·meta — **노드 순서 무변경** ✅  
Sprint 3: deconstruct **prompt + verify** 만 — builder topology 무변경 ✅  
Sprint 4: post-pipeline index + UI — **weaver/skeptic 무변경** ✅  
Sprint 5: fact_checker corpus path — **노드 순서·이름 무변경** ✅  
Sprint 6: post-pipeline recompose — **weaver/skeptic/DAG 무변경** ✅  
Sprint 7: guards + watch UI — **파이프라인 토폴로지 무변경** ✅

### ω-4. 코드베이스 대조

| 주장 | 코드 현황 | Sprint |
|------|-----------|--------|
| `ExtractedSource` meta 없음 | `kind, label, text` only | SP1-META-01 |
| pipeline에 `src.text`만 전달 | `pipeline_batch.py:163` | SP1-META-03 |
| `merge_graph_results` id-only | `state_graph.py:126` | SP2-POL-02, SP2-BRG-01 |
| verify loop 존재, depth rarely >1 | `after_verify.py` | SP3-RECUR-* |
| skeleton module 없음 | — | SP4-IDX-01 ✅ |
| status JSON has fact_checker | `server.py:311` | SP0-FC-01 |

### ω-5. 측정 가능성

모든 Appendix에 **합격식 + 관측 위치** 명시 ✅

### ω-6. PROCESS 확장

Sprint 공통 DoD + Appendix 완료본 = **0-N 미니 사이클** ✅

---

# 구현 착수 순서 (확정)

```
0-5 ✅ (본 문서)
  → Sprint 0 ✅ (Appendix A) — SP0-FC-*
  → Sprint 1 ✅ (Appendix B) — SP1-META-*
  → Sprint 2 ✅ (Appendix C) — SP2-*
  → Sprint 3 ✅ (Appendix D) — SP3-*
  → Sprint 4 ✅ (Appendix E) — SP4-*
  → Sprint 5 ✅ (Appendix G) — SP5-*
  → Sprint 6 ✅ (Appendix H) — SP6-*
  → Sprint 7 ✅ (Appendix I) — SP7-*
```

---

## 코드베이스 링크 (0-5 주석 고정)

| 파일 | STAGE 0-5 / Sprint |
|------|---------------------|
| `web/index.html` | Sprint 0 (FC UI), Sprint 4 (Outline) ✅ |
| `deconstructor/web/server.py` | Sprint 0 status, Sprint 4 `/api/skeleton` ✅ |
| `deconstructor/skeleton/` | Sprint 4 G-SKP-INDEX ✅ |
| `deconstructor/web/extract.py` | Sprint 1 meta |
| `deconstructor/web/pipeline_batch.py` | Sprint 1 provenance, Sprint 2 bridge |
| `deconstructor/models.py` | Sprint 1 AtomicFact fields |
| `deconstructor/viz/state_graph.py` | Sprint 2 merge/bridge |
| `deconstructor/routing/after_verify.py` | Sprint 3 recur |
| `deconstructor/graph/builder.py` | D-06 코어 불변 |
| `tests/test_stage0_acceptance.py` | T-FAST every sprint |
