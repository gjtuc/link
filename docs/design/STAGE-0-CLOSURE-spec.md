# STAGE 0-CLOSURE — 0단계 마무리 (μ 재쪼개기)

> **입력:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) S0-A~F, [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Sprint 0~7 ✅  
> **목적:** Sprint 구현 후 **시나리오 E2E** 로 0-3 AC를 실환경에서 재확인  
> **규칙:** [PROCESS.md](PROCESS.md) — 각 시나리오도 **μ → 구현/스크립트 → 기록** 반복

---

## CLOSURE 목록 (1차)

| ID | 시나리오 | 우선 | μ prefix | 스크립트 | 기록 |
|----|----------|------|----------|----------|------|
| **CL-0-A** | S0-A PDF 1편 | P0 | μ-A-* | `s0a_e2e_run.py` | [S0-A-E2E-RECORD.md](S0-A-E2E-RECORD.md) ✅ |
| **CL-0-B** | S0-B 텍스트 초안 | P0 | μ-B-* | `s0b_e2e_run.py` | S0-B-E2E-RECORD.md |
| **CL-0-C** | S0-C 다중 파일 | P1 | μ-C-* | `s0c_e2e_run.py` | S0-C-E2E-RECORD.md |
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

## B-1. 1차 → μ 재쪼개기

| μ-ID | STAGE-0-2 | 검증 방법 | NON-GOAL |
|------|-----------|-----------|----------|
| **μ-B-ING-01** | B-2-1 | short fixture → `len(sources)==1` | LLM |
| **μ-B-ING-02** | B-2-1 | short chars ≥ 200, no summarize | 요약 모드 |
| **μ-B-ING-03** | B-2-2 | long fixture → `len(sources)>=2` | LLM |
| **μ-B-ING-04** | B-2-2 | long total chars ≈ 원문 (≥8k) | PDF |
| **μ-B-PIPE-01** | B-2-3 | short only pipeline `ok==true` | long×LLM |
| **μ-B-PIPE-02** | B-2-3 | Skeptic edges computed | — |
| **μ-B-SKP-01** | B-2-4 | `gap_count` present (F0-B2: high gap OK) | node count |
| **μ-B-SKP-02** | B-2-4 | `weak_count` or weak list present | — |
| **μ-B-REC-01** | B-2-4 | recompose block exists | full rewrite |
| **μ-B-FC-01** | δ/C-4 | FC mode not hidden | live Tavily |

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

## C-1. μ 재쪼개기

| μ-ID | STAGE-0-2 | 검증 | NON-GOAL |
|------|-----------|------|----------|
| **μ-C-ING-01** | C-2-1 | ≥2 `source_file` | 단일 PDF |
| **μ-C-ING-02** | C-2-1 | ≥2 sources after chunk | — |
| **μ-C-ORC-01** | C-2-2 | `orchestration.merge_mode==batch_corpus` | global DB |
| **μ-C-ORC-02** | C-2-3 | `bridge_count` is int (0 허용) | LLM cross-doc |
| **μ-C-ORC-03** | C-2-3 | subject-match MVP (Ni catalyst) | Skeptic CAUSES |
| **μ-C-UI-01** | C-2-4 | `cross_doc_label` contains 「교차」 | source filter |
| **μ-C-PIPE-01** | — | full batch `ok==true` | — |

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

1. μ-* 표 — 본 문서 + 시나리오별 RECORD.md  
2. `scripts/s0{a,b,c}_e2e_run.py` — exit 0  
3. STAGE-0-2 § A-5/B-5/C-5 **현재 구현** 갱신  
4. PR 본문에 Sprint μ 매핑 + E2E 결과 링크

---

# 다음 (0단계 이후)

| 단계 | 내용 |
|------|------|
| CL-0-D~F | S0-D/E/F μ 스펙 확장 |
| **STAGE 1** | 0-1 계약 유지, 1~10 구현 단계 본격 (밀도·cross-run corpus) |
