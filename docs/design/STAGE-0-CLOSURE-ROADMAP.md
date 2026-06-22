# STAGE 0-CLOSURE — 분기 로드맵 (확정)

> **계약 원칙:** ingest 계약을 **조금만** 어겨도(요약·출처 누락·F0-A2) 분석 결과가 **그럴듯하게** 깨진다.  
> **그래서:** LLM(Phase A) 전 **읽기(Phase R) 게이트** + **분기마다 pytest 증명**.  
> **μ 재쪼개기:** 1차 → μ-ID → pytest/스크립트 → ω → 다음 분기 **하나만** 잠금 해제.  
> **지금 활성:** Branch-0 **MUST**. Branch-1 **완료** (2026-06-22). 2a/2b/3 **잠금 · 착수 금지**.

---

## 활성 분기 (지금)

```
Branch-0  Phase R  pytest + phase_r_regression     ← 지속 MUST
    │
    └─ DONE ──► Branch-1  S0-B/C Phase A E2E ✅     ← 2026-06-22
```

## 잠금 분기 (생각·착수 금지)

| Branch | 내용 | 잠금 사유 |
|--------|------|-----------|
| 2a | μ-A 깊이 | Branch-1 + 분석 이슈 관측 전 |
| 2b | STAGE 1 | 클로저 전 |
| 3 | μ-R edge | 실 PDF/DOCX R fail 관측 전 |

---

## Branch-0 — Phase R (지금 · MUST)

| T-ID | pytest / 명령 | 증명 |
|------|---------------|------|
| T-B0-01 | `tests/test_ingest_foundation.py` | μ-R-* |
| T-B0-02 | `tests/test_branch_gates.py` | S1-READ gate, contract breaks |
| T-B0-03 | `tests/test_stage0_acceptance.py` | AC-ING-* |
| T-B0-04 | `python scripts/phase_r_regression.py` | 통합 (LLM 0) |

**DoD:** 위 전부 exit 0. **ingest touch / PR마다.**

### Branch-0 pytest 핵심 (계약 → 게이트)

| 테스트 | 의미 |
|--------|------|
| `test_branch0_s1_read_blocks_pipeline_no_llm` | R fail → Deconstruct **0회** |
| `test_branch0_mu_r_gate_02_missing_source_file_fails_must` | C-2 살짝 위반 → MUST fail |
| `test_branch0_mu_r_gate_01_f0_a2_blocks_read` | NG-1 symptom → blocking |

---

## Branch-1 — 완료 ✅ (2026-06-22)

**스펙:** [BRANCH-1-spec.md](BRANCH-1-spec.md)

| T-ID | pytest (offline) | manual (quota) |
|------|------------------|----------------|
| T-B1-00 | `test_branch1_prerequisite_s0b/c_phase_r` | — |
| T-B1-01 | `test_branch1_spec_mu_ids_documented` | — |
| T-B1-10 | — | `s0b_e2e_run.py` ✅ |
| T-B1-11 | — | `s0c_e2e_run.py` ✅ |
| T-B1-20 | `pytest tests/test_sprint*.py …` | 회귀 |

**DoD:** S0-B/C Phase A exit 0 + RECORD ✅ — **0단계 클로저 Branch-1 닫힘**

**REG-B1 (2026-06-22, `ee54729`):** Q1 2-pass 후 Branch-1 full 회귀 exit 0 (~542 s). S0-B gap=16 weak=2, S0-C bridge=1 — [BRANCH-1-spec.md](BRANCH-1-spec.md) § REG-B1.

---

## μ 재쪼개기 (분기 공통)

```
1. 분기 1차 목표
2. μ-ID 표 + pytest ID 매핑 (T-B*-**)
3. 구현 (필요 시)
4. pytest PASS → (Branch-1+) manual E2E
5. RECORD + ω → 다음 Branch **하나** 잠금 해제
```

---

## NON-GOALS

- Branch-0 skip  
- Branch-2a/2b/3 선행  
- quota 없이 Branch-1 DoD 인정
