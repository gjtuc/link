# INGEST Foundation — 읽기 확인 → 분석 확인

> **계약:** β-1, C-1, NG-1 — **조금만** 어겨도 Phase A 결과가 그럴듯하게 망가짐 → **R 게이트 필수**  
> **검증:** 분기마다 pytest (`tests/test_branch_gates.py`, `test_ingest_foundation.py`)

> **진행:** 1차 작성 → **μ 재쪼개기 (R/A 2-phase)** → 점검 → 주석 고정  
> **입력:** [STAGE-0-1-product-definition.md](STAGE-0-1-product-definition.md) (β-1~3, C-1, NG-1)  
>         [STAGE-0-3-acceptance-criteria.md](STAGE-0-3-acceptance-criteria.md) (AC-ING-*)  
> **코드:** `deconstructor/web/ingest_verify.py`, `scripts/ingest_read_verify.py`

---

## 왜 읽기 → 분석 순인가

| 단계 | 비유 (ζ) | 시스템 | LLM |
|------|----------|--------|-----|
| **Phase R** | 완성품을 **읽었다** | extract → chunk → meta | **0회** |
| **Phase A** | **부스러기**로 쪼갠다 | Deconstruct → … → Viz | 필요 |

분석(Deconstruct) 전에 **「원문을 제대로 읽었는지」** 를 먼저 증명하지 않으면,  
파이프라인 결과(노드·Gap)는 **읽기 실패(NG-1)** 와 구분할 수 없다.

```
[파일/텍스트] ──Phase R (μ-R-*)──► ReadVerifyReport.ok?
                                        │
                         false ─────────┴──► STOP (S1-READ, no LLM)
                         true  ─────────────► Phase A (μ-A-*, pipeline)
```

---

## Phase R — μ-R-* (읽기 확인)

### R-0 모드 (MUST)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-MODE-01** | AC-ING-02 | `LINK_DOCUMENT_INGEST=document` |
| μ-R-MODE-02 | AC-ING-06 | URL/HTML summarize 경로는 document 검증 **제외** |

### R-1 추출 (MUST)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-EXT-01** | — | 모든 source `text` non-empty |
| μ-R-EXT-02 | — | PDF `document_page_count` ≥ 0 |
| μ-R-EXT-03 | F0-A1 | 추출 0자 → ValueError (extract 단계) |

### R-2 보존 (MUST)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-RET-01** | AC-ING-01 | `sum(chars)/raw ≥ 0.95` (raw 제공 시) |
| **μ-R-RET-02** | AC-NEG-02 | bulk text 유지, 2–5문장 붕괴 아님 |
| **μ-R-GUARD-01** | AC-ING-07 | F0-A2: pages>3 & chars<500 → **blocking** |

### R-3 청크 (MUST/SHOULD)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-CHK-01** | AC-ING-03 | file chars >8k → chunks ≥ 2 |
| **μ-R-CHK-02** | AC-ING-04 | label: `청크 k/n` or `p.x-y` |
| **μ-R-CHK-03** | — | chunk len ≤ DOC_CHUNK + margin |
| **μ-R-CHK-04** | S0-B B-2-1 | ≤2k chars → 1 chunk |

### R-4 메타 (SHOULD → Sprint 1)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-META-01** | AC-ING-05 | `source_file` non-empty |
| **μ-R-META-02** | AC-ING-05 | `chunk_id == make_chunk_id(...)` |
| **μ-R-META-03** | AC-ING-05 | `1 ≤ chunk_index ≤ chunk_total` |
| μ-R-META-03b | — | 동일 file 내 `chunk_total` 일관 |

### R-5 배치 읽기 (SHOULD)

| μ-ID | AC | 검증 |
|------|-----|------|
| **μ-R-BAT-01** | S0-C C-2-1 | ≥2 distinct `source_file` |

---

## Phase A — μ-A-* (분석 확인)

**선행:** `ReadVerifyReport.ok == true`

| μ-ID | AC | 검증 |
|------|-----|------|
| μ-A-PIPE-01 | AC-DEC-01 | `pipeline ok`, no failed_step |
| μ-A-FC-01 | AC-FC-02 | fact_checker mode |
| μ-A-SKP-01 | AC-SKP-03~05 | skeleton gap/strong |
| μ-A-ORC-01 | AC-ORC-02 | bridge_count / 교차 0건 |

상세: [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) (기존 μ-A/B/C → **μ-A** 로 통합)

---

## 실행·테스트

| T-ID | 명령 | Phase | Branch |
|------|------|-------|--------|
| **T-READ-FAST** | `pytest tests/test_ingest_foundation.py tests/test_stage0_acceptance.py` | R | **0** |
| **T-READ-FIX** | `python scripts/ingest_read_verify.py --all` | R | **0** |
| **T-READ-E2E** | `s0{a,b,c}_e2e_run.py --read-only` | R | **0** |
| **T-READ-ALL** | `python scripts/phase_r_regression.py` | R | **0** |
| T-B0-GATE | `pytest tests/test_branch_gates.py` | R | **0** |
| T-ANALYZE-E2E | `s0{b,c}_e2e_run.py` (no flag) | A | **1** |

분기 로드맵: [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md)

---

## 파이프라인 게이트

`pipeline_batch._run_pipeline_batch_inner`:

1. **S1-READ** — `verify_read(sources)` → fail 시 LLM **0회**
2. (기존 S1-GUARD는 μ-R-GUARD-01에 흡수; 단계 로그는 S1-READ)

analyze JSON: `read_verify` 블ock 추가.

---

## ω 점검

- R-phase는 **pytest + phase_r_regression** 으로 MUST 게이트 ✅  
- A-phase는 LLM quota — **Branch-1** 에서만 클로저 DoD  
- μ-R edge (**Branch-3**): 실 PDF/DOCX 실패 관측 후에만 확장  
- μ-A 깊이 (**Branch-2a**): B/C full run 후 분석 이슈 있을 때만

---

## NON-GOALS

- OCR 품질 개선 (별도 Sprint)  
- summarize 모드 제거 (S0-D 레거시)  
- Deconstruct 프롬프트 (Phase A)
