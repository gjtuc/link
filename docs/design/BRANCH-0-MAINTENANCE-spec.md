# Branch-0 — 유지 계약 (MAINT)

> **상태:** μ-MAINT-ω (파도 1)  
> **목적:** B2a 마감 후에도 Branch-0 MUST(Phase R·ingest 게이트)를 **문서·스크립트·pytest**로 잠근다.  
> **금지 (본 파도):** live Gemini E2E, pipeline/DAG 토폴로지 변경.

---

## μ-ID

| μ-ID | 트리거 | 필수 검증 | 금지 |
|------|--------|-----------|------|
| **μ-MAINT-R** | ingest touch — `tests/ingest_manifest.py` → **`INGEST_TOUCH_PATHS`** (authoritative, 중복 정의 금지) | `phase_r_regression.py` exit 0 | Phase A 선행 |
| **μ-MAINT-S** | orchestration touch (`pipeline_batch.py` 등, manifest 목록 참조) | `branch1_regression_smoke.py` exit 0 | — |
| **μ-MAINT-F** | Branch-1 계약 대변경·Q1급 파이프라인 변경 | `branch1_full_e2e.py` exit 0 (~542s) | quota 없이 인정 금지 |
| **μ-MAINT-ω** | 본 spec + health script + sample | offline pytest | live probe/E2E |

---

## ingest touch (manifest 인용)

**단일 출처:** `tests/ingest_manifest.py` — `INGEST_TOUCH_PATHS`

위 경로 중 **하나라도** 변경 시 → **μ-MAINT-R**: `python scripts/phase_r_regression.py` exit 0 **필수** (Phase A로 건너뛰기 금지).

---

## μ-MAINT-02 — Branch-0 health check

**스크립트:** `scripts/branch0_health_check.py`  
**LLM:** 0 (offline + Phase R read-only 경로만)

**순서 (고정):**

1. `python scripts/stage0_reaudit_baseline.py` — exit 0, `mismatches=[]`
2. `python scripts/phase_r_regression.py` — exit 0
3. `pytest tests/test_branch_gates.py tests/test_ingest_foundation.py -q` — exit 0

**산출:** `logs/branch0_health/YYYYMMDD-HHMM-health.json` (각 단계 exit, baseline mismatches)

**금지 (health 스크립트 내):** `branch1_full_e2e`, `b2a_density_*`, capability probe live.

---

## μ-MAINT-ω — offline 검증

| 산출 | 경로 |
|------|------|
| sample | `tests/fixtures/branch0_health_sample.json` |
| pytest | `tests/test_branch0_health.py` |

```bash
python scripts/branch0_health_check.py
python -m pytest tests/test_branch0_health.py tests/test_branch_gates.py -q
python scripts/stage0_reaudit_baseline.py
```

---

## 관련

- [INGEST-FOUNDATION-spec.md](INGEST-FOUNDATION-spec.md)
- [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md) — Branch-0 MUST 지속
- [PROCESS.md](PROCESS.md)
