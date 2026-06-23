# Branch-2b — STAGE 1 (cross-run corpus) — 설계만

> **상태:** **μ-UNLOCK-2b** ✅ — Branch-2b 착수 잠금 해제 (2026-06-23)  
> **선행:** Branch-0 MUST (μ-MAINT-ω), Branch-1 complete, Branch-2a 1차 관측 마감 (μ-B2a-ω), 파도 1~3, **μ-PRE-2b-00**  
> **다음:** **μ-2b-00** — STAGE-1 skeleton / corpus 계약 (구현 설계)

---

## 1차 목표

Branch-2b = **[STAGE 1](STAGE-0-CLOSURE-spec.md)** — 0단계 클로저 이후 **cross-run corpus** 단계.

| 항목 | 내용 |
|------|------|
| 범위 | 세션·런 간 **corpus DB**에 fact/graph를 누적·조회하는 계약 (설계) |
| PR 본문 힌트 | cross-run corpus DB, ingest→Neo4j 영속 경계, batch vs global corpus |
| AC-DEC-02 MUST 검토 | **본 Branch와 분리** — 별도 μ로만 착수 (B2a SHOULD 관측 ≠ MUST 승격) |
| 2a vs 2b | `branch_2_unlocked=true` (2a) **≠** Branch-2b 착수 허용 |

**관련:** [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) · [BRANCH-2a-spec.md](BRANCH-2a-spec.md)

---

## 선행 (DoD before 2b-01 구현)

| # | 조건 | 상태 |
|---|------|------|
| 1 | Branch-0 MUST 지속 — `phase_r_regression.py`, `branch0_health_check.py` | ✅ μ-MAINT-ω |
| 2 | Branch-1 complete — `branch_1_complete=true`, RECORD | ✅ |
| 3 | Branch-2a 1차 관측 마감 — AC-DEC-02 SHOULD 2경로 | ✅ μ-B2a-ω |
| 4 | 파도 1~3 — MAINT, CAT, STAGE0 | ✅ |
| 5 | **μ-PRE-2b-00** 본 spec + offline sample | ✅ (본 문서) |
| 6 | **감독·사용자 승인** | ✅ μ-UNLOCK-2b |
| 7 | **μ-UNLOCK-2b** — `branch_2b_unlocked` 등 잠금 해제 | ✅ |

**μ-2b-00 착수 가능:** 위 1~7 충족. STAGE-1 코드·live E2E는 μ-2b-00 주문부터.

---

## μ-ID (미래 구현 — 전부 [ ] 미착수)

번호는 **설계안**; 구현 주문 시 확정.

| μ-ID | 내용 | 검증 (예정) | 상태 |
|------|------|-------------|------|
| **μ-PRE-2b-00** | Branch-2b 설계 spec + sample | 본 spec + `branch2b_design_sample.json` | ✅ |
| **μ-UNLOCK-2b** | branch_2b 착수 잠금 해제 조건 | `branch_state` + pytest gate | ✅ |
| **μ-2b-00** | STAGE-1 skeleton / corpus 계약 | spec + offline pytest | [ ] |
| **μ-2b-01** | cross-run ingest (설계→구현) | TBD — Neo4j·session 경계 | [ ] |
| **μ-2b-02** | corpus query / UI 힌트 (선택) | TBD | [ ] |
| **μ-2b-ω** | 2b 1차 마감 | sample + `stage0_reaudit_baseline.py` | [ ] |

---

## 잠금 해제 조건 (문서만)

| 필드 | 의미 | 이번 commit |
|------|------|-------------|
| `branch_2_unlocked` | Branch-2a (μ-A 깊이) 열림 | **변경 금지** — 현재 `true` |
| `branch_2b_unlocked` | Branch-2b (STAGE-1) 착수 허용 | **제안만** — 기본 `false`, μ-UNLOCK-2b에서 설정 |
| `branch_2b_design_complete` | 설계 spec·sample 완료 (optional meta) | μ-PRE-2b-00에서 `true` 기록 가능 |

**μ-UNLOCK-2b DoD (예정):**

1. 본 spec + 감독·사용자 서면 승인  
2. `stage0_reaudit_baseline.py` + `phase_r_regression.py` exit 0  
3. `branch_state.json`에 `branch_2b_unlocked=true` — **μ-UNLOCK-2b 전용 commit**  
4. `tests/test_branch_gates.py` — 2b 구현 spec 허용 규칙 갱신  

**금지:** `unlock_branch2.py` 재실행, `branch_2_unlocked` 수동 true로 2b 우회.

---

## NON-GOALS

- **Branch-3** — μ-R edge (실 PDF/DOCX R fail 관측 전)  
- **코어 DAG 토폴로지 변경** (D-06) — 2b도 우회 경로 없이 계약 확장  
- **Q1 2-pass 재설계**  
- **probe/catalog `verified` 일괄 승격** — [Q2-CAPABILITIES-spec.md](Q2-CAPABILITIES-spec.md) § Status policy  
- **AC-DEC-02 MUST 승격** — B2a 관측 링크만; 별도 μ  
- **live Gemini E2E** — unlock 전  
- **`branch1_full_e2e.py`** — 2b 설계 파도에서 재실행 금지  

---

## 관련 링크

- [BRANCH-2a-spec.md](BRANCH-2a-spec.md) — 2a 1차 관측 마감  
- [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) — 분기 로드맵  
- [STAGE-0-CLOSURE-spec.md](STAGE-0-CLOSURE-spec.md) — Branch 2b = STAGE 1  
- [BRANCH-0-MAINTENANCE-spec.md](BRANCH-0-MAINTENANCE-spec.md) — Branch-0 MUST 지속  
- [Q2-CAPABILITIES-spec.md](Q2-CAPABILITIES-spec.md) — catalog status policy  

---

## 오프라인 검증 (μ-PRE-2b-03)

```bash
python -m pytest tests/test_branch2b_design_sample.py tests/test_branch_gates.py -q
```

**sample:** `tests/fixtures/branch2b_design_sample.json`
