# Branch-1 — quota 복구 후 Phase A (0단계 클로저)

> **상태:** **완료** (2026-06-22 — `branch1_full_e2e.py` exit 0)  
> **다음 분기만:** Branch-2a/2b/3 **착수 금지** (로드맵 잠금).  
> **선행:** [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) Branch-0  
> **입력:** [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) μ-A-B/C

---

## 1차 목표

quota 복구 후 **S0-B, S0-C Phase A full E2E** → RECORD 갱신 → **0단계 클로저 닫기**.

---

## μ 재쪼개기 — Phase A (S0-B)

| μ-ID | STAGE-0-2 | 합격식 | pytest |
|------|-----------|--------|--------|
| **μ-A-B-PIPE-01** | B-2-3 | `result.ok == true` | manual E2E |
| **μ-A-B-PIPE-02** | B-2-3 | `edges >= 0` | manual E2E |
| **μ-A-B-SKP-01** | B-2-4 | `gap_count is not None` | manual E2E |
| **μ-A-B-SKP-02** | B-2-4 | `weak_count is not None` | manual E2E |
| **μ-A-B-REC-01** | B-2-4 | `recompose.report_markdown` | manual E2E |
| **μ-A-B-FC-01** | C-4 | `fact_checker.mode` in corpus/stub | manual E2E |

### μ-A-B 선행 (Phase R — Branch-0에서 이미 증명)

| μ-ID | Branch-0 pytest |
|------|-----------------|
| short 1 chunk, long 3 chunks | `test_branch1_prerequisite_s0b_phase_r` |
| char retention | `test_ingest_foundation` + `ingest_read_verify --all` |

---

## μ 재쪼개기 — Phase A (S0-C)

| μ-ID | STAGE-0-2 | 합격식 | pytest |
|------|-----------|--------|--------|
| **μ-A-C-ORC-01** | C-2-2 | `merge_mode == batch_corpus` | manual E2E |
| **μ-A-C-ORC-02** | C-2-3 | `bridge_count` is int | manual E2E |
| **μ-A-C-ORC-03** | C-2-3 | Ni subject bridge ≥0 (0=「교차 0건」OK) | manual E2E |
| **μ-A-C-UI-01** | C-2-4 | `cross_doc_label` contains 교차 | manual E2E |
| **μ-A-C-PIPE-01** | — | `result.ok == true` | manual E2E |

### μ-A-C 선행 (Phase R)

| μ-ID | Branch-0 pytest |
|------|-----------------|
| 2 files ingest | `test_branch1_prerequisite_s0c_phase_r` |

---

## 실행 순서 (quota 복구 후)

```bash
# Branch-0 MUST
python scripts/phase_r_regression.py

# Branch-1 (quota) — single entry
python scripts/branch1_full_e2e.py
```

---

## DoD

- [x] `s0b_e2e_run.py` exit 0 (no `--read-only`)
- [x] `s0c_e2e_run.py` exit 0
- [x] S0-B-E2E-RECORD.md, S0-C-E2E-RECORD.md Phase A ✅
- [x] CLOSURE-ROADMAP Branch-1 ✅

---

## NON-GOALS (Branch-1)

- Branch-2a/2b/3 스펙·구현  
- μ-R edge 선확장  
- μ-A “깊이” 선확장 (분석 이슈 관측 전)

---

## ω 점검

- Phase R은 Branch-0 pytest로 **이미** 증명 — Branch-1은 **A만** 추가  
- F0-B2: Gap 많음 = PASS (약한 뼈대 드러남)
