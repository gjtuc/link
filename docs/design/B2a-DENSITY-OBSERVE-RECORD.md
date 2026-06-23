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

---

## μ-B2a-02 — S0-A PDF (`s0a_paper.pdf`)

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-23 |
| elapsed_sec | **174.0** |
| runs | 1 |
| completed_facts_per_run | **[12]** |
| median_completed_facts | **12.0** |
| ac_dec_02_meets_should | **true** |
| atomic_facts_total | 12 |
| nodes / edges | 17 / 64 |
| pipeline_ok | true |

**B2a-DENSITY-S0A PASS** — S0-A born-digital PDF, AC-DEC-02 SHOULD **충족** (관측).

**로그:** `logs/b2a_density/20260623-1315-b2a-density-s0a-detail.json`

---

## μ-B2a-ω — 1차 관측 마감 (2026-06-23)

| 항목 | 값 |
|------|-----|
| S0-B median | **5.5** (`b268c08`) |
| S0-A PDF median | **12.0** (`51c3afa`) |
| AC-DEC-02 SHOULD | **양쪽 충족** |
| L3 SCAN | R2a + R2b ✅ |
| live 재실행 | **없음** (문서 ω) |

**판정:** Branch-2a **1차 관측 마감** — AC-DEC-02 텍스트·PDF born-digital 관측 기록 완료. Branch-2b **잠금 유지**.
