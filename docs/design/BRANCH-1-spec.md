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

---

## REG-B1 — Q1 후 회귀 (2026-06-22, `ee54729`)

Q1 2-pass Dreamer (`285ef9f`) 적용 후 Branch-1 DoD(S0-B/C Phase A full) 재증명. **exit 0 = 합격** (관측 숫자 변동은 Q1·LLM 분산 가능, 실패 조건 아님).

| μ-ID | 내용 | 스크립트 / 산출 |
|------|------|-----------------|
| **μ-REG-B1a** | Phase R 선행 게이트 | `python scripts/phase_r_regression.py` → exit 0 |
| **μ-REG-B1b** | Branch-1 full (Gemini) | `python scripts/branch1_full_e2e.py` → exit 0, ~542 s |
| **μ-REG-B1c** | 관측 스냅샷 | `scripts/branch1_regression_snapshot.py` → `logs/branch1_regression/*-regression.json` (gitignore) |
| **μ-REG-B1ω** | 주석 고정 | 본 §, 스크립트 헤더, `tests/fixtures/branch1_regression_sample.json` |

### 관측 (2026-06-22, 재실행 없이 기록)

| 시나리오 | 관측 | 이전 Branch-1 (2026-06-22) | delta |
|----------|------|---------------------------|-------|
| **S0-B** | gap=16, weak=2, `pipeline_ok`, fc=corpus | gap=20, weak=3 | gap −4, weak −1 |
| **S0-C** | bridge=1, `merge_mode=batch_corpus`, 교차 1건 | 동일 | — |

**branch_state:** `branch_1_complete=true`, `branch_2_unlocked=false`  
**RECORD:** [S0-B-E2E-RECORD.md](S0-B-E2E-RECORD.md) 갱신 (gap/weak). S0-C 숫자 동일 → 미변경.  
**pytest:** `tests/test_branch1_regression_sample.py`, `tests/test_branch_gates.py`  
**fixture 샘플:** `tests/fixtures/branch1_regression_sample.json` (로그 gitignore 대체)
