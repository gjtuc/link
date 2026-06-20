# Sprint 7 — Watch / Guards (G-DEC-WARN, G-ING-GUARD, G-SKP-05) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix I  
> **AC:** AC-DEC-04, AC-ING-07, AC-SKP-05  
> **선행:** Sprint 4 ✅ (skeleton), Sprint 3 ✅ (partial_run debug)  
> **상태:** 구현 완료 (μ-ING~TST ✅) — SP7-DOC-01

---

## 1. 한 줄 목표

**P2 감시:** partial_run **메인 UI 경고**, F0-A2 **ingest 차단**, NG-2 **skeleton 판정 힌트**.  
**코어 DAG 무변경** — pre/post pipeline guards + UI only.

---

## 2. μ — SP7 재쪼개기 (4 레이어)

```
μ-ING  ingest guard   SP7-ING-01~03
μ-DEC  partial_run    SP7-DEC-01~03
μ-SKP  NG-2 hint      SP7-SKP-01~02
μ-API  watch block    SP7-API-01~02
μ-UI   경고 패널      SP7-UI-01~03
μ-TST  검증           SP7-TEST-01~05
```

| μ-ID | SP7 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **ING-01** | ING-01 | `document_page_count` on PDF ExtractedSource | unit |
| **ING-02** | ING-02 | F0-A2: pages>3 ∧ chars<500 → blocking | pytest |
| **ING-03** | ING-03 | pre-pipeline S1-GUARD fail JSON | pipeline_batch |
| **DEC-01** | DEC-01 | `collect_partial_run_warnings(states)` | unit |
| **DEC-02** | DEC-02 | debug `deconstruct_batch.partial_run_runs` | debug_report |
| **DEC-03** | DEC-03 | index `#watch-panel` partial_run banner | index.html |
| **SKP-01** | SKP-01 | nodes>20 ∧ strong=0 → NG-2 hint | unit |
| **SKP-02** | SKP-02 | AC-SKP-05: hint references Gap/Strong | message text |
| **API-01** | API-01 | analyze `watch` block | pipeline_batch |
| **API-02** | API-02 | blocking → `ok:false` + watch | API |
| **UI-01** | UI-01 | `#watch-panel` severity colors | CSS |
| **UI-02** | UI-02 | debug.html partial_run per run | debug.html |
| **UI-03** | UI-03 | idle clears watch | JS |
| **TST-01~05** | TEST | guards + batch + UI wiring | pytest |

---

## 3. AC closure

| AC | Before | Sprint 7 |
|----|--------|----------|
| AC-DEC-04 | ⚠️ debug only | ✅ index + debug |
| AC-ING-07 | ⚠️ 수동 | ✅ auto guard + test |
| AC-SKP-05 | ✅ Sprint 4 | ✅ NG-2 watch hint |

---

## 4. F0-A2 규칙 (ING-02)

PDF `document_page_count > 3` **AND** aggregated `source_file` chars `< 500`  
→ **blocking** (summarize/추출 실패 의심, NG-1).

---

## 5. NON-GOALS

- partial_run 자동 수정  
- ingest summarize 모드 제거  
- 코어 파이프라인 변경

---

## 6. DoD

- [x] `tests/test_sprint7_watch.py` PASS
- [x] sprint0~6 + stage0 PASS
- [x] Appendix I + AC 갱신

---

## 7. 파일 맵

| 파일 | μ |
|------|---|
| `deconstructor/guards/ingest_guard.py` | ING-* |
| `deconstructor/guards/batch_warnings.py` | DEC-*, SKP-* |
| `deconstructor/web/extract.py` | ING-01 |
| `deconstructor/web/pipeline_batch.py` | ING-03, API-* |
| `deconstructor/web/debug_report.py` | DEC-02 |
| `web/index.html`, `web/debug.html` | UI-* |
| `tests/test_sprint7_watch.py` | TST-* |
