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
| **μ-CAT-01** | Status policy (승격 규칙) | 본 spec § Status policy |
| **μ-CAT-02** | Probe evidence 표 (실측) | 본 spec § Evidence matrix |
| **μ-CAT-03** | offline policy pytest | `tests/test_capabilities_policy.py` |
| **μ-CAT-ω** | 파도 2 마감 | 본 표 + sample + handoff §7 |

**관측 (2026-06-22):** verified ≥6, catalog 시드 6건, `/api/capabilities` 200, UI 모달 문자열 wired.

---

## Status policy (μ-CAT-01)

catalog·capability 항목의 `status` 승격은 **추측·probe 1회만으로 하지 않는다.**

| status | 승격 조건 | 금지 |
|--------|-----------|------|
| **verified** | E2E/REG 통과 + spec 관측 기록 + **감독 승인** | probe 1회만으로 `verified` |
| **untested** | catalog 시드·부분 probe·evidence 보강 | evidence 없이 `verified` |
| **unsupported** | extract 미구현·형식 미지원 확정 | probe 성공만으로 `unsupported` 해제 |

**코드:** `deconstructor/capabilities/build.py` — `cap-*`는 branch_state·RECORD·ingest; `cat-*`는 `catalog.py` 시드 (`untested`\|`unsupported`만).

### `cat-scanned-pdf` — `untested` 유지 (2026-06-23)

| evidence | probe μ-ID | 관측 요지 |
|----------|------------|-----------|
| not_true_scan fallback | μ-PROBE-03 | exit 2, scan PDF 없음 (`20260622-2309`) |
| born-digital 503 | μ-PROBE-SCAN-ω | exit 2, `gemini_503` — 스캔 품질 아님 (`20260623-0116`) |
| scan_no_text_layer | μ-PROBE-SCAN-R2a | exit 2, `empty_extract`, 0 chars/1p (`20260623-1100`) |
| scan_ocr_noisy | μ-PROBE-SCAN-R2b | exit 0, pipeline_ok, 6630 chars/2p (`20260623-1130`) |

**`untested` 유지 이유:** 상반된 probe 결과(차단 vs 통과), 스캔·OCR 품질 스펙트럼 미완결, Branch-1급 E2E/REG·감독 승인 없음. evidence는 `catalog.py`·본 표에 **유지·보강**하되 status 승격은 **별도 μ**.

---

## Evidence matrix (μ-CAT-02, 실측만)

상세 절차·로그: [CAPABILITY-PROBE-spec.md](CAPABILITY-PROBE-spec.md)

| probe μ-ID | cat-id | evidence (실측) | catalog status |
|------------|--------|-----------------|----------------|
| μ-PROBE-01 (R0) | `cat-neo4j-off` | exit 0, pipeline_ok, ~291.6s (`20260622-2315`) | untested |
| μ-PROBE-R1 | `cat-neo4j-off` | exit 0, pipeline_ok, ~96.2s, `LINK_DISABLE_NEO4J_AUTO_START` (`20260623-0024`) | untested |
| μ-PROBE-02 | `cat-pdf-triple` | exit 0, 3 source_file, pipeline_ok, ~496s (`20260622`) | untested |
| μ-PROBE-03 | `cat-scanned-pdf` | exit 2, `not_true_scan` (`20260622-2309`) | untested |
| μ-PROBE-SCAN-ω | — (catalog 무변경) | born-digital, exit 2, `gemini_503`, ~3059.7s (`20260623-0116`) | — |
| μ-PROBE-SCAN-R2a | `cat-scanned-pdf` | handwriting, `scan_no_text_layer`, exit 2, 0 chars/1p (`20260623-1100`) | untested |
| μ-PROBE-SCAN-R2b | `cat-scanned-pdf` | watson-crick, `scan_ocr_noisy`, exit 0, 6630 chars/2p (`20260623-1130`) | untested |
| — | `cat-file-10mb` | probe 미실행 | untested |
| — | `cat-gemini-429` | probe 미실행 (Branch-1 quota 관측만) | untested |
| — | `cat-opju-origin` | extract 미구현 | unsupported |

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
