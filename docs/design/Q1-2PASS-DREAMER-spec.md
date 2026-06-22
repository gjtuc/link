# Q1 — 2-pass Dreamer (양끝 + Gap, 옵션 A)

> **상태:** 구현 (POST-BRANCH-1 Q1)  
> **선행:** Branch-1 `branch_1_complete=true`, Phase R 게이트  
> **Gap 규칙:** `deconstructor/skeleton/rules.py` → `find_gaps` 재사용

---

## 목적

1차에서 **extracted(파란)** 사실만 Skeptic → 검증된 CAUSES 뼈대.  
2차 Dreamer는 **좁힌 fact id**에서 Flash→Pro → Fact-Checker → Skeptic(2차) → Weaver.

1-pass `verify→Dreamer→FC→Skeptic`는 Q1에서 **2-pass**로 대체. 코어 블록 유지, Skeptic **2회**.

---

## 그래프 (enable_dreamer=True)

```
deconstruct → verify ⇄ loop
                ↓
          skeptic_pass1  (extracted only)
                ↓
            dreamer      (pass2 sources)
                ↓
          fact_checker
                ↓
            skeptic      (extracted + pass2 promoted)
                ↓
            weaver → END
```

**Before (1-pass):** `verify → dreamer → fact_checker → skeptic`  
**After (Q1):** `verify → skeptic_pass1 → dreamer → fact_checker → skeptic`

---

## μ-ID → 검증

| μ-ID | 내용 | pytest / 스크립트 |
|------|------|-------------------|
| **μ-Q1-01** | 본 spec + 입력 규칙 | (문서) |
| **μ-Q1-02** | `select_pass2_source_facts` | `tests/test_q1_pass2_inputs.py` |
| **μ-Q1-03** | builder 2-pass 토폴로지 | `tests/test_q1_two_pass_dry_run.py` |
| **μ-Q1-04** | dreamer pass2 source + 로그 | dry-run smoke |
| **μ-Q1-05** | 회귀 | `phase_r_regression.py`, branch gates |
| **μ-Q1-06** | dry-run smoke | `test_q1_two_pass_dry_run.py` |
| **μ-Q1-07** | live read-only (선택) | `s0b_e2e_run.py --read-only` |
| **μ-V5-01** | `dreamer_pass2_breadth_probe.py` (2-pass pass2 Flash) | 스크립트 |
| **μ-V5-02** | s0b/s0a live 3-run 실측 vs DIV03 | `logs/dreamer_breadth/pass2-*-summary.json` |
| **μ-V5-03** | `test_dreamer_pass2_breadth_diversity.py` | pytest offline + `@live` |

---

## 2차 Dreamer 입력 선택 (`pass2_inputs.py`)

**INCLUDE**

1. **양끝:** pass1 `verified_edges_pass1` CAUSES 각 edge의 `source_fact_id` + `target_fact_id` 중 **chain interior 제외**  
   - interior = CAUSES in-degree ≥1 **and** out-degree ≥1  
2. **Gap (옵션 A):** `find_gaps(nodes, edges)` 결과 `id` — conclusion-like, CAUSES in-degree 0

**EXCLUDE**

- 비-Gap **orphan extracted** (`find_weak` → `orphan_extracted`와 동일)
- **중간 노드** (interior, 위 정의)
- inferred / pending / dropped
- 화살표(edge 객체) 자체

---

## State 키 (최소)

| 키 | 설정 노드 |
|----|-----------|
| `verified_edges_pass1` | skeptic_pass1 |
| `pass2_gap_nodes` | skeptic_pass1 (`find_gaps`) |
| `dreamer_log` | dreamer (`pass2_source_count`, `pass2_gap_count`) |

---

## NON-GOALS (Q1)

- Q2/Q3 capabilities UI  
- Branch-2/3 / STAGE-1  
- Flash/Pro 로직 변경 (입력 선택만)
