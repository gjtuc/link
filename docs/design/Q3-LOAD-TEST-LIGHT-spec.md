# Q3 — 부하 테스트 경량 마감 (POST-BRANCH-1)

> **상태:** 완료 (경량 — UI 힌트만)  
> **선행:** Q2 `c472879`, μ-POST-Q2-0 `e669add`  
> **범위 밖:** 전체 부하 probe 자동화·Branch-2·DAG 변경

---

## 목적

Q2 `catalog.py` 시드(6건) + `/api/capabilities` `summary.untested`를 UI에 노출.  
사용자가 **「아직 안 해본 테스트 N가지」** 를 상시 확인하고, 클릭 시 기존 `cap-warn-modal`로 상세 목록.

전체 부하 자동화(E2E probe 루프)는 **이번 μ 범위 밖**.

---

## μ-ID → 검증

| μ-ID | 내용 | pytest / 산출 |
|------|------|----------------|
| **μ-Q3-01** | UI 「아직 안 해본 테스트 N가지」 힌트 | `tests/test_capabilities_ui.py` — `#cap-probe-hint` |
| **μ-Q3-02** | 본 spec — Q2 catalog = Q3 probe 후보 | (문서) |
| **μ-Q3-03** | POST-BRANCH-1 큐 삭제 | `POST-BRANCH-1-WORK-QUEUE.md` 제거 commit |

**관측 (2026-06-22, baseline):** `summary.untested=5`, `unsupported=1`, UI 힌트 `아직 안 해본 테스트 5가지 · 미지원 1가지`.

---

## Q2 catalog = Q3 probe 후보

정의: `deconstructor/capabilities/catalog.py` (Q2에서 시드 6건).  
향후 probe 실행 시 `scripts/log_capability_run.py` → `logs/capability_runs/` (gitignore).

| id | status | 유형 |
|----|--------|------|
| `cat-pdf-triple` | untested | 개수 |
| `cat-opju-origin` | unsupported | 형식 |
| `cat-scanned-pdf` | untested | 내용 |
| `cat-file-10mb` | untested | 크기 |
| `cat-neo4j-off` | untested | 환경 |
| `cat-gemini-429` | untested | 환경 |

---

## UI 동작

1. 로드 시 `GET /api/capabilities` → `updateCapProbeHint(summary)`
2. `untested > 0` → 「아직 안 해본 테스트 N가지」 (`#cap-probe-hint`)
3. `unsupported > 0` → 「· 미지원 M가지」追加
4. 클릭 → `cap-warn-modal` (기존 Q2 모달)
5. 분석 시작 → `ensureCapabilityAck()` 유지

---

## 실행·회귀

```bash
python scripts/stage0_reaudit_baseline.py
python scripts/phase_r_regression.py
pytest tests/test_capabilities_ui.py tests/test_capabilities_build.py -q
```

관련: [Q2-CAPABILITIES-spec.md](Q2-CAPABILITIES-spec.md)
