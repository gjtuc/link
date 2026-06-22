# B2a — AC-DEC-02 density observe E2E 기록

> **μ-ID:** μ-B2a-01  
> **실행:** `python scripts/b2a_density_observe_e2e.py`  
> **픽스처:** S0-B (`s0b_draft_short.txt` + `s0b_draft_long.txt`, 4 runs)  
> **스펙:** [BRANCH-2a-spec.md](BRANCH-2a-spec.md)

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-23 |
| OS | Windows 10 |
| Neo4j | 로컬 bolt |
| Fact-Checker | `corpus` |
| elapsed_sec | 678.6 |

---

## AC-DEC-02 관측 (SHOULD median≥5)

| 항목 | 값 |
|------|-----|
| runs | 4 |
| completed_facts_per_run | [5, 5, 13, 6] |
| median_completed_facts | **5.5** |
| ac_dec_02_meets_should | **true** |
| runs_with_depth_gt_1 | 0 |
| atomic_facts_total | 29 |
| pipeline_ok | true |

---

## 판정

**B2a-DENSITY PASS** — pipeline ok; AC-DEC-02 SHOULD median≥5 **충족** (관측).

**로그:** `logs/b2a_density/20260623-0004-b2a-density-detail.json`
