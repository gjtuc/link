# S0-B E2E 기록 — 보고서 텍스트 초안

> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) § S0-B  
> **μ 스펙:** [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) § μ-B-*  
> **실행:** `python scripts/s0b_e2e_run.py` (전체) / `--ingest-only` (μ-B-ING)

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-20 |
| 픽스처 | `s0b_draft_short.txt` (517c), `s0b_draft_long.txt` (11289c) |

---

## μ-B 체크리스트

| μ-ID | 결과 | 관측 |
|------|------|------|
| μ-B-ING-01 | ✅ | short → 1 chunk |
| μ-B-ING-02 | ✅ | short ≥200 chars, no summarize |
| μ-B-ING-03 | ✅ | long → 2+ chunks |
| μ-B-ING-04 | ✅ | long total 12088 chars retained |
| μ-B-PIPE-01 | ⏸ | Gemini 429 quota (dreamer step) |
| μ-B-PIPE-02 | ⏸ | pipeline blocked |
| μ-B-SKP-01~02 | ⏸ | skeleton pending full run |
| μ-B-REC-01 | ⏸ | recompose pending |

---

## 판정

**μ-B-ING PASS** — B-2-1, B-2-2 ingest AC 충족.  
**μ-B-PIPE PENDING** — quota 복구 후 `python scripts/s0b_e2e_run.py` 재실행.

---

## 재실행

```bash
python scripts/generate_s0bc_fixtures.py
python scripts/s0b_e2e_run.py          # full (LLM)
python scripts/s0b_e2e_run.py --ingest-only  # ingest μ only
```
