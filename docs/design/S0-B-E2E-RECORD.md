# S0-B E2E 기록 — 보고서 텍스트 초안

> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) § S0-B  
> **μ 스펙:** [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) § μ-B-*  
> **실행:** `python scripts/s0b_e2e_run.py` (전체) / `--ingest-only` (μ-B-ING)

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-22 |
| 픽스처 | `s0b_draft_short.txt` (517c), `s0b_draft_long.txt` (11289c) |

---

## μ-B 체크리스트

| μ-ID | 결과 | 관측 |
|------|------|------|
| μ-B-ING-01 | ✅ | short → 1 chunk |
| μ-B-ING-02 | ✅ | short ≥200 chars, no summarize |
| μ-B-ING-03 | ✅ | long → 2+ chunks |
| μ-B-ING-04 | ✅ | long total 12088 chars retained |
| μ-B-PIPE-01 | ✅ | `pipeline_ok=true` |
| μ-B-PIPE-02 | ✅ | pipeline completed (short full run) |
| μ-B-SKP-01 | ✅ | `gap_count=16` |
| μ-B-SKP-02 | ✅ | `weak_count=2` |
| μ-B-REC-01 | ✅ | recompose report present |
| μ-A-B-FC-01 | ✅ | `fact_checker.mode=corpus` |

---

## 판정

| Phase | Branch | 결과 |
|-------|--------|------|
| **R** | 0 | ✅ `verify_read` + `--read-only` |
| **A** | 1 | ✅ PASS |

**Branch-0:** PASS. **Branch-1:** PASS (2026-06-22, `branch1_full_e2e.py`).

Flash breadth diversity (s0b short, 3-run avg): dup=0.0, uniq_subj=1.0, mech_sim=0.063 (μ-DR-DIV-03 PASS, 1-pass 전체 completed).

Flash breadth pass2 (s0b short, 3-run avg): dup=0.0, uniq_subj=1.0, mech_sim=0.053 (μ-V5 DIV03 PASS). pass1_edges=0, pass2_sources=5 (전부 Gap).

Q1 2-pass smoke (short live, 2026-06-22): pass1_edges=1, pass2_gap=3, pass2_sources=4, promoted=5, skeleton gap=7 weak=1, fc=corpus (Branch-1 gap=20·weak=3과 별개).

Q1 후 REG-B1 (2026-06-22): Branch-1 full 재증명 exit 0 — gap=16 weak=2 pipeline_ok fc=corpus (이전 gap=20 weak=3, Q1 2-pass·LLM 분산 가능).

---

## 재실행

```bash
python scripts/generate_s0bc_fixtures.py
python scripts/s0b_e2e_run.py          # full (LLM)
python scripts/s0b_e2e_run.py --ingest-only  # ingest μ only
```
