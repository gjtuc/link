# Sprint 3 — Deconstruct Depth (G-DEC-DENS, G-DEC-RECUR) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix D  
> **AC:** AC-DEC-02 (SHOULD), AC-DEC-03 (SHOULD)  
> **선행:** Sprint 1 ✅ (per-chunk meta), Sprint 2 ✅  
> **상태:** 구현 완료 (μ-PRM~TST ✅) — SP3-DOC-01

---

## 1. 한 줄 목표

**β-2:** non-atomic crumb → Verify → Deconstruct **재루프** 가 실제로 돌고, 긴 청크에서 **fact 밀도** 를 LLM·휴리스틱·관측으로 끌어올린다.  
**코어 DAG 토폴로지 불변** (D-06).

---

## 2. μ — SP3 재쪼개기 (4 레이어)

```
μ-PRM  프롬프트   SP3-RECUR-01, SP3-DENS-01
μ-HEU  휴리스틱  SP3-RECUR-02  (LLM 오판 보정)
μ-OBS  관측      SP3-RECUR-03, SP3-DENS-02
μ-TST  검증      SP3-TEST-01, SP3-TEST-02
```

| μ-ID | SP3 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **PRM-01** | RECUR-01 | `is_atomic=False` when compound (and/comma/multi-clause) | prompt text |
| **PRM-02** | RECUR-01 | `is_atomic=True` only single entity + single transition | prompt text |
| **PRM-03** | DENS-01 | `min_facts_for_text(n)` → user prompt hint | unit |
| **PRM-04** | DENS-01 | deconstruct_node → `invoke_fact_list(..., min_facts_hint=)` | code path |
| **HEU-01** | RECUR-02 | `looks_compound(fact)` — subject/state markers | unit |
| **HEU-02** | RECUR-02 | `apply_compound_heuristic` before partition | verify_node |
| **HEU-03** | RECUR-02 | True→False only; never upgrade to atomic | test |
| **OBS-01** | RECUR-03 | `summarize_single_state`: recursion_depth, max, partial_run | debug JSON |
| **OBS-02** | DENS-02 | per-run `completed_facts` + chunk_id in run summary | debug JSON |
| **OBS-03** | DENS-02 | `build_pipeline_debug.deconstruct_batch` median, depth>1 count | debug JSON |
| **TST-01** | TEST-01 | compound heuristic → non_atomic stays in extracted | pytest |
| **TST-02** | TEST-01 | dry_run pipeline `recursion_depth >= 2` | pytest |
| **TST-03** | TEST-01 | `min_facts_for_text(8000) >= 5` | pytest |
| **TST-04** | TEST-02 | `@pytest.mark.expensive` LLM E2E optional | skip default |

---

## 3. 밀도 힌트 (PRM-03) — 튜닝表

| 입력 chars | `min_facts_hint` | AC-DEC-02 관계 |
|------------|------------------|----------------|
| < 500 | 2 | 짧은 URL/문장 |
| 500–1999 | 3 | — |
| 2000–7999 | 5 | **median 목표** |
| ≥ 8000 | 8 | 논문 청크 |

SHOULD — LLM 미달 시 **실패 아님**; debug `median_completed_facts` 로 관측.

---

## 4. Compound 휴리스틱 (HEU-01) — 보수적 규칙

`is_atomic=True` 이지만 아래면 **False 로 강등** (Verify 전):

- `subject` 에 ` and `, ` & `, `, `, ` / `
- `state_change` 에 ` and ` 또는 `;`

**NON-GOAL:** subject 길이만으로 강등 (NG-2).

---

## 5. 재귀 경로 (기존 코드 확인)

```
deconstruct → verify → route_after_verify
  extracted 비음 & depth < cap → deconstruct (R-2)
  depth >= cap → skeptic (R-3, partial_run)
```

Stub dry_run: pass0 `is_atomic=False` → **depth≥2** (TST-02).  
Live: PRM + HEU 로 non_atomic 비율 ↑.

---

## 6. AC closure

| AC | Before | Sprint 3 |
|----|--------|----------|
| AC-DEC-02 | ⚠️ ~1/chunk | ⚠️→**관측+힌트** (median in debug; E2E expensive) |
| AC-DEC-03 | ❌ | ✅ depth>1 in dry_run + heuristic tests |

AC-DEC-02 full ✅ 는 **expensive E2E** 또는 추후 prompt 튜닝; 0-3 「SHOULD·튜닝 가능」 유지.

---

## 7. ω — 설계 자기 점검

| ω | 검증 |
|---|------|
| ω-1 | builder.py 노드 순서 무변경 ✅ |
| ω-2 | HEU 보수적 — false negative > false positive ✅ |
| ω-3 | Sprint 1 chunk_id in per-run debug ✅ |
| ω-4 | TST 회귀 sprint0~2 ✅ |

---

## 8. DoD

- [x] `tests/test_sprint3_deconstruct_depth.py` PASS
- [x] sprint0~2 + stage0 PASS
- [x] AC-DEC-03 ✅; AC-DEC-02 debug median documented

---

## 9. 파일 맵

| 파일 | μ |
|------|---|
| `deconstruct/prompts.py` | PRM-01,02 |
| `deconstruct/density_hints.py` | PRM-03 (신규) |
| `deconstruct/llm_runner.py` | PRM-04 |
| `deconstruct/node.py` | PRM-04 |
| `verify/compound_heuristic.py` | HEU-* (신규) |
| `verify/node.py` | HEU-02 |
| `web/debug_report.py` | OBS-* |
