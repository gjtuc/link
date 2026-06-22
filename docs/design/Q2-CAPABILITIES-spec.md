# Q2 — 능력·한계 카드 (capabilities)

> **상태:** 구현 (POST-BRANCH-1 Q2)  
> **선행:** Branch-1 `branch_1_complete=true`, μ-REG-B1+ω (`b5ef97e`)  
> **금지:** Branch-2/3/STAGE-1, `branch_2_unlocked` 수동 true, 코어 DAG 변경

---

## 목적

`branch_state` + E2E RECORD + ingest 계약 + 부하 catalog → **capabilities JSON** + 감독 말투 `human_line`.  
업로드/분석 전 UI에서 ✅ 확인됨 / ⚠️ 미검증 / ❌ 미지원을 보여 주고 [그래도 실행][나중에] 선택.

---

## μ-ID → 검증

| μ-ID | 내용 | pytest / 스크립트 |
|------|------|-------------------|
| **μ-Q2-01** | 본 spec + JSON 스키마 | (문서) |
| **μ-Q2-02** | `build_capabilities()` offline | `tests/test_capabilities_build.py` |
| **μ-Q2-03** | GET `/api/capabilities` | `tests/test_capabilities_api.py` |
| **μ-Q2-04** | 업로드 전 경고 모달 | `tests/test_capabilities_ui.py` |
| **μ-Q2-05** | probe run log | `scripts/log_capability_run.py`, `tests/test_capabilities_log.py` |
| **μ-Q2-06** | 회귀 | `phase_r_regression.py` + branch gates |
| **μ-POST-Q2-0** | Q2 후 ω-0 baseline 확장 | `stage0_reaudit_baseline.py` — PASS 2026-06-22 |

**관측 (2026-06-22):** verified ≥6, catalog 시드 6건, `/api/capabilities` 200, UI 모달 문자열 wired.

---

## 항목 JSON 스키마

각 capability 객체:

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | 고유 ID (`cap-*`, `cat-*`) |
| `status` | string | `verified` \| `untested` \| `unsupported` |
| `human_line` | string | 감독 말투 한국어 1문장 |
| `source` | string | 근거 (`branch_state`, RECORD, `ingest_manifest`, `catalog`) |
| `evidence` | string | 관측·설명 (추측 금지) |

최상위 payload: `generated_at`, `branch_state`, `capabilities[]`, `summary{verified,untested,unsupported}`.

---

## API

**선택:** 전용 `GET /api/capabilities` (채택) — status와 분리해 capabilities 전체를 캐시·테스트하기 쉽다.  
`/api/status`는 Neo4j·FC 등 런타임만 유지.

---

## Q3 catalog 시드 (부하·미지원 — JSON/코드, md 남발 금지)

| id | status | human_line (요지) | 유형 |
|----|--------|-------------------|------|
| `cat-pdf-triple` | untested | PDF 3개 동시 업로드 | 개수 |
| `cat-opju-origin` | unsupported | `.opju` Origin 프로젝트 | 형식 |
| `cat-scanned-pdf` | untested | 스캔·표만 PDF | 내용 |
| `cat-file-10mb` | untested | 10MB+ 단일 파일 | 크기 |
| `cat-neo4j-off` | untested | Neo4j 꺼진 상태 | 환경 |
| `cat-gemini-429` | untested | Gemini quota 429 | 환경 |

정의: `deconstructor/capabilities/catalog.py`  
로그: `logs/capability_runs/YYYYMMDD-HHMM-<id>.json` (gitignore → `capability_run_sample.json`)

---

## 실행

```bash
python -c "from deconstructor.capabilities import build_capabilities; import json; print(json.dumps(build_capabilities(), ensure_ascii=False, indent=2))"
python scripts/log_capability_run.py --id cap-s0b-draft --script s0b_e2e_run.py --exit 0
pytest tests/test_capabilities_build.py tests/test_capabilities_api.py tests/test_capabilities_ui.py tests/test_capabilities_log.py -q
python scripts/phase_r_regression.py
```

**Q3 경량 마감:** [Q3-LOAD-TEST-LIGHT-spec.md](Q3-LOAD-TEST-LIGHT-spec.md) — catalog 시드 = probe 후보, UI 「N가지」 힌트.
