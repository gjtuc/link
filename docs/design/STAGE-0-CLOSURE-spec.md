# STAGE 0-CLOSURE — 0단계 마무리 (μ 재쪼개기)

> **기초 순서:** [INGEST-FOUNDATION-spec.md](INGEST-FOUNDATION-spec.md) — **Phase R → Phase A**  
> **분기 로드맵:** [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) (**확정**)  
> **입력:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) S0-A~F

---

## CLOSURE 목록 (1차)

| ID | 시나리오 | 우선 | μ prefix | 스크립트 | 기록 |
|----|----------|------|----------|----------|------|
| **CL-0-A** | S0-A PDF 1편 | P0 | μ-R + μ-A | `s0a_e2e_run.py` | [S0-A-E2E-RECORD.md](S0-A-E2E-RECORD.md) R✅ A✅ |
| **CL-0-B** | S0-B 텍스트 초안 | P0 | μ-R + μ-A | `s0b_e2e_run.py` | [S0-B-E2E-RECORD.md](S0-B-E2E-RECORD.md) R✅ A⏸ |
| **CL-0-C** | S0-C 다중 파일 | P1 | μ-R + μ-A | `s0c_e2e_run.py` | [S0-C-E2E-RECORD.md](S0-C-E2E-RECORD.md) R✅ A⏸ |
| CL-0-D | S0-D URL | P2 | μ-D-* | (Later) | — |
| CL-0-E | S0-E human 가설 | P1 | μ-E-* | (Later) | — |
| CL-0-F | S0-F debug | P2 | μ-F-* | pytest + manual | — |

---

# μ-A — S0-A (완료 ✅)

| μ-ID | AC | 관측 | 합격 |
|------|-----|------|------|
| μ-A-ING-01 | A-2-1 | `total_extracted_chars >= 500` | ✅ |
| μ-A-ING-02 | A-2-1 | `document_page_count >= 1` | ✅ |
| μ-A-PIPE-01 | A-2-2 | `result.ok == true` | ✅ |
| μ-A-PIPE-02 | A-2-2 | `atomic_facts_total >= 1` | ✅ 12 |
| μ-A-GRA-01 | A-2-3 | `nodes >= 1`, `edges >= 0` | ✅ 17/32 |
| μ-A-FC-01 | A-2-4 | `fact_checker.mode in (corpus, stub)` | ✅ corpus |
| μ-A-SKP-01 | A-2-5 | `skeleton.gap_count` non-null | ✅ 6 |
| μ-A-SKP-02 | A-2-5 | `skeleton.strong_chain_count` non-null | ✅ 50 |
| μ-A-REC-01 | A-2-5 | `recompose.report_markdown` | ✅ |
| μ-A-WCH-01 | — | `watch.has_partial_run == false` | ✅ |

---

# μ-B — S0-B (보고서 텍스트)

## B-0. Phase 분리

| Phase | μ prefix | Branch | 상태 |
|-------|----------|--------|------|
| **R** | μ-R-* (INGEST-FOUNDATION) | 0 | ✅ `--read-only` |
| **A** | μ-A-B-* below | 1 | ⏸ quota |

## B-1. Phase A → μ 재쪼개기 (Branch-1)

| μ-ID | STAGE-0-2 | 검증 방법 | NON-GOAL |
|------|-----------|-----------|----------|
| **μ-A-B-PIPE-01** | B-2-3 | short pipeline `ok==true` | long×LLM |
| **μ-A-B-PIPE-02** | B-2-3 | Skeptic edges computed | — |
| **μ-A-B-SKP-01** | B-2-4 | `gap_count` present (F0-B2 OK) | node count |
| **μ-A-B-SKP-02** | B-2-4 | `weak_count` present | — |
| **μ-A-B-REC-01** | B-2-4 | recompose block | full rewrite |
| **μ-A-B-FC-01** | δ/C-4 | FC mode visible | live Tavily |

Phase R ingest (μ-B-ING-*) → **μ-R-CHK/META** 로 검증 (`verify_read`, Branch-0).

## B-2. 픽스처 (μ-FIX-B)

| 파일 | 역할 |
|------|------|
| `tests/fixtures/s0b_draft_short.txt` | 비약·결론 위주 (~800자) |
| `tests/fixtures/s0b_draft_long.txt` | 청크 분해 검증 (~9k자) |

생성: `python scripts/generate_s0bc_fixtures.py`

## B-3. ω 점검

- B-2-2 long은 **ingest-only** — 비용·시간 절감 (μ-B-PIPE는 short만)  
- F0-B2: Gap 많음 = **PASS** (뼈대 약함 드러남)

---

# μ-C — S0-C (다중 파일)

## C-0. Phase 분리

| Phase | μ prefix | Branch | 상태 |
|-------|----------|--------|------|
| **R** | μ-R-BAT-*, μ-R-META-* | 0 | ✅ |
| **A** | μ-A-C-* below | 1 | ⏸ quota |

## C-1. Phase A → μ 재쪼개기 (Branch-1)

| μ-ID | STAGE-0-2 | 검증 | NON-GOAL |
|------|-----------|------|----------|
| **μ-A-C-ORC-01** | C-2-2 | `merge_mode==batch_corpus` | global DB |
| **μ-A-C-ORC-02** | C-2-3 | `bridge_count` int (0 OK) | LLM cross-doc |
| **μ-A-C-ORC-03** | C-2-3 | Ni catalyst subject bridge | Skeptic CAUSES |
| **μ-A-C-UI-01** | C-2-4 | `cross_doc_label` 「교차」 | source filter |
| **μ-A-C-PIPE-01** | — | `ok==true` | — |

Phase R multi-file (μ-C-ING-*) → **μ-R-BAT-01** (`verify_read`, Branch-0).

## C-2. 픽스처 (μ-FIX-C)

| 파일 | 역할 |
|------|------|
| `s0c_paper.txt` | Ni catalyst 주 subject |
| `s0c_memo.txt` | 동일 subject cross-file |

## C-3. ω 점검

- bridge 0건이면 **「교차 0건」** — AC-ORC-02 충족 (투명)  
- NG-2: nodes만 많음 ≠ 성공 — **bridge_count 또는 explicit 0** 필수

---

# CLOSURE DoD

1. **Branch-0** `phase_r_regression.py` — exit 0 (지속)  
2. **Branch-1** S0-B/C Phase A full + RECORD ✅  
3. μ-* 표 + STAGE-0-2 § B-5/C-5 갱신  
4. [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) Branch 상태 ✅

---

# 다음 (분기 잠금)

| Branch | 조건 | 내용 |
|--------|------|------|
| **1** | quota | S0-B/C Phase A → 클로저 닫기 |
| **2a** | B/C 후 분석 이슈 | μ-A 깊이 |
| **2b** | 클로저 + R stable | STAGE 1 |
| **3** | 실 PDF/DOCX R fail | μ-R edge |
