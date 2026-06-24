# Branch-2a — μ-A 깊이 (AC-DEC-02 밀도 관측)

> **상태:** **μ-B2a-ω 완료** — Branch-2a **1차 관측 마감** (2026-06-23)  
> **선행:** μ-PROBE-01~03 + SCAN R2a/R2b, `unlock_branch2.py`  
> **잠금 유지:** Branch-2b (STAGE-1), Branch-3 (μ-R edge)

---

## μ-ID

| μ-ID | 내용 | 검증 |
|------|------|------|
| **μ-B2a-01** | AC-DEC-02 median 관측 E2E (S0-B) | `scripts/b2a_density_observe_e2e.py` ✅ |
| **μ-B2a-02** | S0-A PDF AC-DEC-02 밀도 추가 관측 | `b2a_density_s0a_observe_e2e.py` ✅ |
| **μ-B2a-03** | ROADMAP Branch-2a 행 + baseline | `STAGE-0-CLOSURE-ROADMAP.md` ✅ |
| **μ-B2a-ω** | Branch-2a 1차 관측 마감 (문서·sample) | 본 spec + `b2a_closure_sample.json` ✅ |

---

## μ-B2a-01 — density observe E2E ✅

**입력:** S0-B fixtures (`s0b_draft_short.txt` + `s0b_draft_long.txt` → 4 runs)

**관측:** `pipeline_debug.deconstruct_batch.median_completed_facts` (AC-DEC-02 proxy)

**합격:** Phase R ok + `pipeline_ok=true`. median≥5 는 **SHOULD** — 미달이어도 exit 0.

**기록:** [B2a-DENSITY-OBSERVE-RECORD.md](B2a-DENSITY-OBSERVE-RECORD.md) — median=**5.5**, per-run `[5,5,13,6]`, commit `b268c08`

**산출:**
- `logs/b2a_density/YYYYMMDD-HHMM-b2a-density-detail.json`
- `logs/capability_runs/YYYYMMDD-HHMM-b2a-density-observe.json`

---

## μ-B2a-02 — S0-A PDF density observe E2E ✅

**입력:** S0-A fixture (`s0a_paper.pdf` → 1 run)

**관측:** `pipeline_debug.deconstruct_batch.median_completed_facts` (AC-DEC-02 proxy)

**합격:** Phase R ok + `pipeline_ok=true`. median≥5 는 **SHOULD** — 미달이어도 exit 0.

| 항목 | 값 (`20260623-1315`) |
|------|----------------------|
| runs | 1 |
| completed_facts_per_run | **[12]** |
| median_completed_facts | **12.0** |
| ac_dec_02_meets_should | **true** |
| atomic_facts_total | 12 |
| nodes / edges | 17 / 64 |
| elapsed_sec | **174.0** |
| pipeline_ok | true |

**기록:** [B2a-DENSITY-OBSERVE-RECORD.md](B2a-DENSITY-OBSERVE-RECORD.md) § μ-B2a-02

**산출:**
- `logs/b2a_density/YYYYMMDD-HHMM-b2a-density-s0a-detail.json`
- `logs/capability_runs/YYYYMMDD-HHMM-b2a-density-s0a-observe.json`

---

## μ-B2a-ω — Branch-2a 1차 관측 마감 ✅

**목적:** μ-B2a-01·02 + L3 SCAN(R2a/R2b) 관측을 **문서·sample로 잠금** — live E2E 재실행 없음.

| 항목 | 관측 (기록만) |
|------|----------------|
| S0-B median | **5.5** (`b268c08`, per-run `[5,5,13,6]`) |
| S0-A PDF median | **12.0** (`51c3afa`, per-run `[12]`) |
| AC-DEC-02 SHOULD (≥5) | **양쪽 충족** (관측) |
| L3 ingest edge | SCAN R2a `empty_extract`, R2b `scan_ocr_noisy` |
| Branch-2b | **잠금 유지** |
| live E2E 재실행 | **금지** (본 ω) |

**오프라인:** `tests/fixtures/b2a_closure_sample.json`, `tests/test_b2a_closure.py`

**기록:** [B2a-DENSITY-OBSERVE-RECORD.md](B2a-DENSITY-OBSERVE-RECORD.md) · [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md)

---

## 선행 (Phase 1)

- `cat-neo4j-off`, `cat-pdf-triple`, `cat-scanned-pdf` probe logs
- [CAPABILITY-PROBE-spec.md](CAPABILITY-PROBE-spec.md)

---

## NON-GOALS

- Branch-2b / STAGE-1
- Branch-3 / μ-R edge 확장
- 코어 DAG 토폴로지 변경

---

## 실행

```bash
python scripts/b2a_density_observe_e2e.py
python scripts/b2a_density_observe_e2e.py --skip-phase-r   # batch 내 재실행
python scripts/b2a_density_s0a_observe_e2e.py            # μ-B2a-02 S0-A PDF
python scripts/b2a_density_s0a_observe_e2e.py --skip-phase-r
```
