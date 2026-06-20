# STAGE 0-3 — 성공 기준 (Acceptance Criteria) (완료본)

> **진행 상태:** 1차 작성 → 재쪼개기(τ) → 점검·수정 → **주석 고정 완료**  
> **입력:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) (S0-*, A0-*, F0-*)  
>         [STAGE-0-1-product-definition.md](STAGE-0-1-product-definition.md) (C-*, NG-*)  
> **다음:** `STAGE-0-4-current-vs-target.md` (본 문서 AC-* 통과/미통과 매트릭스) — **0-3 완료**  
> **다음 단계:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) — **Sprint 0**

---

## 0-3 목적

0-2 시나리오의 Then을 **측정·판정 가능**한 조건으로 바꾼다.  
각 AC-* 는 **관측 위치**(API·UI·테스트)·**합격식**·**우선순위**·**현재 상태**를 가진다.

### 우선순위 레벨

| Level | 의미 | 0-2 대응 |
|-------|------|----------|
| **MUST** | 0단계 계약 위반 = 제품 실패 | P0 S0-A, S0-B |
| **SHOULD** | 목표 시나리오, 다음 마일스톤 | P1 S0-C, S0-E |
| **MAY** | 부가·레거시 경로 | P2 S0-D, S0-F |

### 판정 기호

| 기호 | 의미 |
|------|------|
| ✅ PASS | 현재 코드·UI로 검증 가능 |
| ⚠️ PARTIAL | 일부만 충족 |
| ❌ FAIL | 미구현 |
| 🔜 | 구현 단계 명시 (1~10) |

---

## A. Ingest (ζ-1, C-1, NG-1)

| AC-ID | Level | S0 | 조건 (합격) | 관측 | 상태 |
|-------|-------|-----|-------------|------|------|
| **AC-ING-01** | MUST | A,B | PDF ingest: `sum(source.chars) / pdf_extracted_chars ≥ 0.95` | `sources[].chars`, pypdf | ✅ |
| **AC-ING-02** | MUST | A,B | `LINK_DOCUMENT_INGEST=document` 시 LLM summarize **호출 0회** | extract_tracked steps: `Gemini 요약` 없음 | ✅ |
| **AC-ING-03** | MUST | A | PDF >8k chars → `len(sources) ≥ 2` 청크 | extract_batch | ✅ |
| **AC-ING-04** | MUST | A | 청크 라벨에 페이지 또는 `청크 k/n` | `ExtractedSource.label` | ✅ |
| **AC-ING-05** | SHOULD | A,C | fact에 `source_file, page_range, chunk_id` (C-2) | AtomicFact meta | ✅ Sprint 1 |
| **AC-ING-06** | MAY | D | HTML URL → summarize 허용, chars <2k typical | url_sources_from_fetch | ✅ |
| **AC-ING-07** | MUST | A | **F0-A2** 위반: document PDF chars <500 & pages>3 → FAIL | S1-GUARD | ✅ Sprint 7 |

**AC-ING-01 측정 예 (당신 PDF):** 63,693 / 63,714 ≈ 0.999 ✅

---

## B. Deconstruct·Verify (ζ-2, β-2, A-2-2)

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-DEC-01** | MUST | A,B | 분석 `ok:true` & `failed_step` 없음 | `/api/analyze/result` | ✅ |
| **AC-DEC-02** | SHOULD | A,B | 청크당 `completed_facts ≥ 5` (median) | pipeline_debug.deconstruct_batch | ⚠️ 힌트+관측 (Sprint 3) |
| **AC-DEC-03** | SHOULD | A,B | `recursion_depth > 1` 비율 >0 (non-atomic) | pipeline_debug | ✅ Sprint 3 (dry_run+heuristic) |
| **AC-DEC-04** | MUST | A,B | `partial_run=true` 시 UI/debug **경고** | index `#watch-panel` + debug | ✅ Sprint 7 |

---

## C. Dreamer·Fact-Checker (ζ-3, ζ-5, C-4, NG-3)

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-FC-01** | MUST | A,B,D | `/api/status`: `fact_checker` ∈ {stub,live,corpus} | JSON | ✅ |
| **AC-FC-02** | MUST | A,B | stub→「미검증」; corpus→「문서 내부 검증」(C-4 full) | index.html status | ✅ Sprint 5 |
| **AC-FC-03** | MUST | A,B | promoted 노드 `source_type=inferred`, 색 노랑/초록 (γ) | graph legend | ✅ |
| **AC-FC-04** | MUST | A | 논문 모드: Tavily **0 호출** (`tavily_disabled:true`) | config/status | ✅ |
| **AC-FC-05** | MAY | D | live + `NG-3` 라벨 「웹 검색 검증」 | status | ✅ Sprint 5 |

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-DR-01** | SHOULD | A,B | Dreamer enabled, `dreamer_promoted ≥ 0` per run | sources[] | ✅ |
| **AC-DR-02** | SHOULD | E | human 가설 POST → 그래프 노드 추가 | `/api/human-hypothesis` | ✅ |

---

## D. Skeptic·因→과 (ζ-3, ζ-4, γ)

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-SKP-01** | MUST | A,B | `verified_edges` 존재 가능, pyvis CAUSES 표시 | graph | ✅ |
| **AC-SKP-02** | MUST | A,B | dropped ghost ✕ 노드 **숨기지 않음** (δ) | graph legend | ✅ |
| **AC-SKP-03** | SHOULD | A,B | **Gap** count: in-degree 0 on conclusion-like facts (C-3) | skeleton index | ✅ Sprint 4 |
| **AC-SKP-04** | SHOULD | A,B | **Strong** chain count ≥1 when paper has clear 因→과 | skeleton index | ✅ Sprint 4 |
| **AC-SKP-05** | MUST | A,B | **NG-2**: PASS ≠ `nodes > N`; 판정은 AC-SKP-03/04 | skeleton + watch NG-2 | ✅ Sprint 4,7 |

---

## E. Orchestration·다중 파일 (S0-C, 2단계)

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-ORC-01** | MUST | C | N files → N×chunks pipeline runs | steps S4-* | ✅ |
| **AC-ORC-02** | SHOULD | C | `bridge_edges` count 또는 UI 「교차 0건」 | orchestration JSON | ✅ Sprint 2 |
| **AC-ORC-03** | SHOULD | C | duplicate subject merge 정책 문서화 | design | ✅ Sprint 2 |
| **AC-ORC-04** | MUST | C | **F0-C2** merge-only → **PARTIAL** 명시 | orchestration.merge_mode | ✅ Sprint 2 |

---

## F. Presentation·Debug (NG-4, S0-F, ε-1)

| AC-ID | Level | S0 | 조건 | 관측 | 상태 |
|-------|-------|-----|------|------|------|
| **AC-UI-01** | MUST | A,B | 분석 후 graph iframe 로드 | index.html | ✅ |
| **AC-UI-02** | MUST | A,B | 진행률·`failed_step` 표시 | progress API | ✅ |
| **AC-UI-03** | SHOULD | A,B | ingest chars / chunk count 결과 JSON | `sources[].chars` | ✅ |
| **AC-UI-04** | SHOULD | A,B | **Outline/Claim tree** (NG-4) | UI `#skeleton-outline` | ✅ Sprint 4 |
| **AC-UI-05** | SHOULD | A,B | **Skeleton Health** panel (C-3) | UI `#skeleton-health` | ✅ Sprint 4 |
| **AC-DBG-01** | MAY | F | debug: completed, orphan, FC mode | `/api/debug/pipeline` | ✅ |
| **AC-DBG-02** | MAY | F | `failed_step` 재현 가능 | steps[] | ✅ |

---

## G. 재조립 (C-5, ε) — 0-3 범위 밖

| AC-ID | Level | 조건 | 상태 |
|-------|-------|------|------|
| **AC-REC-01** | — | 재조리 텍스트 출력 없음이 **정상** (0-1 C-5) | ✅ by design |
| **AC-REC-02** | SHOULD | ε-2 report + ε-3 narrative + ε-4 rewrite outline (`recompose` + UI) | ✅ Sprint 6 |

---

## H. 안티패턴 회귀 (F0-* → AC-NEG-*)

| AC-NEG | F0 | 합격 (테스트가 기대하는 것) |
|--------|-----|---------------------------|
| **AC-NEG-01** | F0-A2 | document PDF + summarize → **test fails** |
| **AC-NEG-02** | F0-B1 | long text → chars preserved |
| **AC-NEG-03** | F0-A1 | empty PDF → `ok:false`, step S2-DOC-* |
| **AC-NEG-04** | F0-C1 | no duplicate UUID same label policy (future) |

---

# 0-1 C-* → AC-* 통합 매핑

| C-* | AC-* |
|-----|------|
| C-1 | AC-ING-01,02,03,07 |
| C-2 | AC-ING-05 |
| C-3 | AC-SKP-03,04, AC-UI-05 |
| C-4 | AC-FC-01,02,03 |
| C-5 | AC-REC-01 (negative acceptance) |

---

# 0-3 자기 점검 — 재쪼개기 (τ)

### τ-1. 측정 가능성

| AC | τ-1 판정 | 조치 |
|----|----------|------|
| AC-ING-01 | ✅ numeric ratio | — |
| AC-DEC-02 | ⚠️ threshold 5는 가설 | 「SHOULD, 튜닝 가능」 명시 ✅ |
| AC-SKP-03 | ✅ skeleton index | — | — |
| AC-ORC-02 | ✅ bridge + UI | — | — |

### τ-2. MUST 과다

- 0-3 MUST = **계약 깨짐**만 (ingest, FC 표시, graph 로드, no false verified)
- DEC-02, SKP-03/04 → **SHOULD** (품질 목표)

### τ-3. A0-* 커버리지

| A0 | AC |
|----|-----|
| A0-A | ING-*, DEC-01, FC-*, SKP-01~02, UI-01~03 |
| A0-B | ING-02,03, SKP-03, FC-02 |
| A0-C | ORC-* |
| A0-D | ING-06, FC-05 |
| A0-E | DR-02 |
| A0-F | DBG-* |

### τ-4. 0-4 진입 데이터

- 각 AC-* 의 ✅/⚠️/❌ → **0-4 gap 테이블** 1:1  
- MUST FAIL 목록 = **P0 구현 백로그**

### τ-5. 테스트 연결

- `tests/test_stage0_acceptance.py` — AC-ING, AC-NEG 문서화 테스트  
- E2E PDF fixture — AC-DEC-02 (optional, expensive)

---

# MUST PASS 최소 세트 (0단계 출시 게이트)

P0 논문·보고서 시나리오(S0-A,B)에 **지금 당장** 요구:

1. AC-ING-01, 02, 03, 04  
2. AC-DEC-01  
3. AC-FC-01, 03, 04  
4. AC-SKP-01, 02  
5. AC-UI-01, 02, 03  
6. AC-REC-01  
7. AC-NEG-01, 02 (회귀)

**SHOULD 미달** (DEC-02) → 0-4 gap, 단계 3 튜닝. SKP-03/04, UI-04/05 → ✅ Sprint 4.

---

# 0-4 진입 시 참조

- MUST PASS vs SHOULD → 우선순위 백로그  
- ⚠️ PARTIAL → 개선 티켓  
- AC-NEG → CI 회귀  

---

## 코드베이스 링크 (0-3 주석 고정)

| 파일 | STAGE 0-3 |
|------|-----------|
| `tests/test_stage0_acceptance.py` | AC-ING, AC-NEG |
| `deconstructor/web/debug_report.py` | AC-DBG, DEC proxy |
| `deconstructor/web/extract.py` | AC-ING 주석 |
| `docs/design/STAGE-0-2-user-scenarios.md` | 0-3 입력 |
