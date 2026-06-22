# S0-C E2E 기록 — 다중 파일 교차 因→과

> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) § S0-C  
> **μ 스펙:** [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) § μ-C-*  
> **실행:** `python scripts/s0c_e2e_run.py` / `--ingest-only`

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-22 |
| 픽스처 | `s0c_paper.txt`, `s0c_memo.txt` |

---

## μ-C 체크리스트

| μ-ID | 결과 | 관측 |
|------|------|------|
| μ-C-ING-01 | ✅ | 2 distinct `source_file` |
| μ-C-ING-02 | ✅ | ≥2 sources |
| μ-C-ORC-01 | ✅ | `merge_mode=batch_corpus` (C-2-2) |
| μ-C-ORC-02 | ✅ | `bridge_count=1` |
| μ-C-ORC-03 | ✅ | Ni catalyst subject bridge |
| μ-C-UI-01 | ✅ | `cross_doc_label` = 교차 1건 |
| μ-A-C-PIPE-01 | ✅ | `pipeline_ok=true` |

---

## 판정

| Phase | Branch | 결과 |
|-------|--------|------|
| **R** | 0 | ✅ μ-R-BAT-01, ingest 2 files |
| **A** | 1 | ✅ PASS |

**Branch-0:** PASS. **Branch-1:** PASS (2026-06-22, `branch1_full_e2e.py`).

```bash
python scripts/generate_s0bc_fixtures.py
python scripts/s0c_e2e_run.py --ingest-only
python scripts/s0c_e2e_run.py
python scripts/s0c_e2e_run.py --read-only
```
