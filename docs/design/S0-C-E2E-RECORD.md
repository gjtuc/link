# S0-C E2E 기록 — 다중 파일 교차 因→과

> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) § S0-C  
> **μ 스펙:** [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) § μ-C-*  
> **실행:** `python scripts/s0c_e2e_run.py` / `--ingest-only`

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-20 |
| 픽스처 | `s0c_paper.txt`, `s0c_memo.txt` |

---

## μ-C 체크리스트 (ingest-only)

| μ-ID | 결과 | 관측 |
|------|------|------|
| μ-C-ING-01 | ✅ | 2 distinct `source_file` |
| μ-C-ING-02 | ✅ | ≥2 sources |
| μ-C-ORC-01~03 | ⏸ | full pipeline pending (LLM quota) |
| μ-C-UI-01 | ⏸ | `cross_doc_label` after batch |

---

## 판정

| Phase | Branch | 결과 |
|-------|--------|------|
| **R** | 0 | ✅ μ-R-BAT-01, ingest 2 files |
| **A** | 1 | ⏸ quota |

**Branch-1:** `python scripts/s0c_e2e_run.py` (full).

```bash
python scripts/generate_s0bc_fixtures.py
python scripts/s0c_e2e_run.py --ingest-only
python scripts/s0c_e2e_run.py
```
