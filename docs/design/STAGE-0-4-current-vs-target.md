# STAGE 0-4 — 현재 vs 목표 Gap (완료본)

> **진행 상태:** 1차 작성 → 재쪼개기(υ) → 점검·수정 → **주석 고정 완료**  
> **입력:** [STAGE-0-3-acceptance-criteria.md](STAGE-0-3-acceptance-criteria.md) (AC-* ✅/⚠️/❌)  
>         [STAGE-0-1-product-definition.md](STAGE-0-1-product-definition.md) (C-*, 구현 단계 1~10)  
> **다음:** `STAGE-0-5-implementation-roadmap.md` (본 문서 G-* → Sprint) — **0-4 완료**  
> **다음 단계:** **Sprint 0** (Appendix A — G-FC-UI)

---

## 0-4 목적

0-3 Acceptance의 **상태 열**을 **구현 갭**으로 변환한다.

- **현재(Current):** 코드·UI·테스트로 관측되는 동작  
- **목표(Target):** 0-1 계약 + 0-3 AC 합격식  
- **갭(Gap):** Target − Current (한 줄)  
- **로드맵 단계:** 1~10 (0-1 C-* 표와 대화에서 합의한 마일스톤)

---

## 구현 단계 참조 (1~10)

| 단계 | 이름 | 핵심 산출 | 관련 AC |
|------|------|-----------|---------|
| **1** | Document ingest | 요약 없이 청크·출처 메타 | ING-* ✅, ING-05 ❌ |
| **2** | Corpus·교차 링크 | 다중 파일 fact pool, bridge_edges | ORC-02,03 |
| **3~4** | Deep Deconstruct | non-atomic 재귀, 청크당 fact 밀도 | DEC-02,03 |
| **6** | Corpus Fact-Checker | 논문용 내부 검증 (Tavily 대체) | FC-02,05 |
| **7** | Skeleton index | Gap/Strong/Weak 규칙 계산 | SKP-03,04 |
| **9** | Claim tree UI | Outline + Skeleton Health | UI-04,05 |
| **10** | Re-compose | 재조리 텍스트 | REC-02 |

**1단계:** ingest·청크 — **대부분 ✅** (출처 메타만 미완)  
**2~9단계:** 품질·표현·다중 문서 — **0-4 백로그**

---

# Gap 매트릭스 (AC → Current → Target)

## A. MUST — 계약 (P0 게이트)

| AC | Current | Target | Gap | 단계 | 우선 |
|----|---------|--------|-----|------|------|
| AC-ING-01~04 | ✅ PASS | 원문 ≥95%, no summarize, multi-chunk, labels | — | 1 ✅ | — |
| AC-DEC-01 | ✅ PASS | analyze ok, no failed_step | — | — | — |
| AC-FC-01 | ✅ PASS | status JSON stub/live | — | — | — |
| **AC-FC-02** | ✅ corpus + stub UI | corpus→「문서 내부 검증」 | — | Sprint 5 | ✅ |
| AC-FC-03,04 | ✅ PASS | inferred 색, Tavily 0 | — | — | — |
| AC-SKP-01,02 | ✅ PASS | CAUSES, dropped ✕ | — | — | — |
| AC-UI-01~03 | ✅ PASS | graph, progress, chars | — | — | — |
| AC-REC-01 | ✅ by design | 재조리 없음 = 정상 | — | 10 | — |
| AC-NEG-01,02 | ✅ tests | 회귀 테스트 | — | 1 | CI |

**P0 MUST 게이트 판정:** **통과** (AC-FC-02 ✅ Sprint 0).

---

## B. SHOULD — 품질·뼈대 (P1 백로그)

| AC | Current | Target | Gap | 단계 | 우선 |
|----|---------|--------|-----|------|------|
| **AC-ING-05** | ❌ fact에 source_file/chunk 없음 | C-2 provenance on AtomicFact | **메타 갭** | 1b | ✅ Sprint 1 |
| **AC-DEC-02** | ⚠️ ~1/chunk | median ≥5 (SHOULD) | **밀도 갭** | Sprint 3 | ⚠️ 힌트+debug |
| **AC-DEC-03** | ❌ recursion_depth≈1 | non-atomic 재분해 >0 | **재귀 갭** | Sprint 3 | ✅ |
| **AC-DEC-04** | ✅ index + debug watch | — | — | Sprint 7 | ✅ |
| **AC-SKP-03** | ✅ Gap count in skeleton index | — | — | Sprint 4 | ✅ |
| **AC-SKP-04** | ✅ Strong chain ≥1 (fixture) | — | — | Sprint 4 | ✅ |
| **AC-SKP-05** | ✅ Health panel + SKP-03/04 | — | — | Sprint 4 | ✅ |
| **AC-UI-04** | ✅ Outline panel | — | — | Sprint 4 | ✅ |
| **AC-UI-05** | ✅ Skeleton Health panel | — | — | Sprint 4 | ✅ |
| AC-DR-01,02 | ✅ | Dreamer + human hypothesis | — | — | — |

---

## C. 다중 파일 (S0-C, 2단계)

| AC | Current | Target | Gap | 단계 | 우선 |
|----|---------|--------|-----|------|------|
| AC-ORC-01 | ✅ N×chunks runs | — | — | 2 | — |
| **AC-ORC-02** | ✅ bridge + UI | bridge_edges 또는 「교차 0건」 | — | Sprint 2 | ✅ |
| **AC-ORC-03** | ✅ | duplicate subject merge 정책 | — | Sprint 2 | ✅ |
| **AC-ORC-04** | ✅ merge_mode | F0-C2: merge-only 한계 UI | — | Sprint 2 | ✅ |

---

## D. PARTIAL·감시 (⚠️)

| AC | Current | Target | Gap | 조치 |
|----|---------|--------|-----|------|
| AC-ING-07 | ✅ S1-GUARD | F0-A2 blocking | — | Sprint 7 |
| AC-FC-02 | ✅ index.html badge | — | Sprint 0 |
| AC-DEC-04 | ✅ watch panel | main UI warning | — | Sprint 7 |
| AC-SKP-05 | ✅ | Health panel Gap/Strong/Weak | — | — |

---

# G-* — Gap ID (재쪼개기)

| G-ID | AC | Gap 한 줄 | 단계 | 우선 |
|------|-----|-----------|------|------|
| **G-FC-UI** | AC-FC-02 | stub/corpus/live UI badges | Sprint 0,5 | ✅ |
| **G-FC-CORPUS** | AC-FC-02 full | corpus FC vs extracted pool | Sprint 5 | ✅ |
| **G-ING-META** | AC-ING-05 | AtomicFact source_file/page/chunk | Sprint 1 | ✅ |
| **G-DEC-DENS** | AC-DEC-02 | 청크당 fact median ≥5 | Sprint 3 | ⚠️ |
| **G-DEC-RECUR** | AC-DEC-03 | Verify non-atomic 재분해 | Sprint 3 | ✅ |
| **G-SKP-INDEX** | AC-SKP-03,04 | skeleton Gap/Strong index | Sprint 4 | ✅ |
| **G-REC-COMPOSE** | AC-REC-02 | ε-2~4 recompose post-pipeline | Sprint 6 | ✅ |
| **G-UI-SKELETON** | AC-UI-04,05 | Outline + Health panel | Sprint 4 | ✅ |
| **G-ORC-BRIDGE** | AC-ORC-02 | cross-doc bridge_edges | Sprint 2 | ✅ |
| **G-ORC-POLICY** | AC-ORC-03 | subject dedup 정책 | Sprint 2 | ✅ |
| **G-ORC-LABEL** | AC-ORC-04 | merge-only 한계 표시 | Sprint 2 | ✅ |
| **G-DEC-WARN** | AC-DEC-04 | partial_run main UI | Sprint 7 | ✅ |
| **G-ING-GUARD** | AC-ING-07 | F0-A2 ingest guard | Sprint 7 | ✅ |

---

# 백로그 순서 (0-4 권장)

### Sprint 0 — P0-quick (1~2일)

1. **G-FC-UI** — `index.html` status bar: stub → 「미검증 가설」  
2. CI: `pytest tests/test_stage0_acceptance.py` 유지

### Sprint 1 — 1b ingest 메타 (단계 1 잔여)

3. **G-ING-META** — Deconstruct 입력에 chunk_id 전달 → AtomicFact meta

### Sprint 2 — 단계 2 (S0-C)

4. **G-ORC-BRIDGE**, **G-ORC-LABEL**, **G-ORC-POLICY**

### Sprint 3 — 단계 3~4 (Deconstruct 깊이)

5. **G-DEC-DENS**, **G-DEC-RECUR**

### Sprint 4 — 단계 7 + 9 (뼈대 UI)

6. **G-SKP-INDEX** → **G-UI-SKELETON**

### Later

7. 단계 6 corpus FC, 단계 10 재조립 (REC-02)

---

# υ — 0-4 자기 점검

### υ-1. Gap ↔ AC 1:1

- 0-3의 ⚠️/❌ AC-* → G-* 또는 「—」 (PASS)  
- 누락 없음 ✅

### υ-2. 단계 번호 일관성

- 0-1 C-* 표·대화 로드맵(1,2,3~4,6,7,9,10)과 정렬 ✅  
- 「1b」= 1단계 잔여(메타만)

### υ-3. MUST vs SHOULD

- MUST FAIL **0건** → P0 게이트 **열림**  
- SHOULD 갭 = Sprint 1~4

### υ-4. 측정 가능성

- 각 G-* 는 AC 합격식 또는 UI 요소로 **완료 판정** 가능  
- G-DEC-DENS: expensive E2E optional (SHOULD)

### υ-5. NON-GOALS 준수

- NG-4 → G-UI-SKELETON (force graph only ≠ 목표)  
- NG-2 → G-SKP-INDEX (node count ≠ 성공)

---

# MUST PASS vs Gap (0-3 게이트 재확인)

| 0-3 MUST PASS | 0-4 상태 |
|---------------|----------|
| ING-01~04 | ✅ 닫힘 |
| DEC-01 | ✅ |
| FC-01,03,04 | ✅ |
| FC-02 | ✅ Sprint 0 |
| SKP-01,02 | ✅ |
| UI-01~03 | ✅ |
| REC-01 | ✅ |
| NEG-01,02 | ✅ |

**결론:** S0-A/B P0 시나리오 **실행 가능**. 품질·뼈대·다중 파일은 G-* 백로그.

---

# 0-5 진입 시 참조

- G-* 우선순위 → 마일스톤 일정·담당 모듈  
- Sprint 0 (G-FC-UI) = **다음 구현 착수 후보**  
- AC-* 재검증: 각 Sprint 완료 시 0-3 표 「상태」 열 갱신

---

## 코드베이스 링크 (0-4 주석 고정)

| 파일 | STAGE 0-4 |
|------|-----------|
| `deconstructor/web/index.html` | G-FC-UI, G-UI-SKELETON (target) |
| `deconstructor/web/server.py` | `/api/status` — FC stub 관측 |
| `deconstructor/graph/builder.py` | G-SKP-INDEX (future) |
| `deconstructor/web/pipeline_batch.py` | G-ORC-BRIDGE (future merge) |
| `tests/test_stage0_acceptance.py` | P0 gate 회귀 |
