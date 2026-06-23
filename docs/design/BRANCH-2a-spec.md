# Branch-2a — μ-A 깊이 (AC-DEC-02 밀도 관측)

> **상태:** μ-B2a-01·02 **완료** (ω 마감)  
> **선행:** μ-PROBE-01~03, `unlock_branch2.py`  
> **잠금 유지:** Branch-2b (STAGE-1), Branch-3 (μ-R edge)

---

## μ-ID

| μ-ID | 내용 | 검증 |
|------|------|------|
| **μ-B2a-01** | AC-DEC-02 median 관측 E2E | `scripts/b2a_density_observe_e2e.py` ✅ |
| **μ-B2a-02** | S0-A PDF AC-DEC-02 밀도 추가 관측 | `b2a_density_s0a_observe_e2e.py` ✅ |
| **μ-B2a-03** | ROADMAP Branch-2a 행 | `STAGE-0-CLOSURE-ROADMAP.md` + baseline |

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
