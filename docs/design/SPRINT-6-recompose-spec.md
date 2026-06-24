# Sprint 6 — Re-compose (G-REC-COMPOSE) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix H  
> **AC:** AC-REC-02 (ε-2~4)  
> **선행:** Sprint 4 ✅ (skeleton), Sprint 5 ✅ (FC mode meta)  
> **상태:** 구현 완료 (μ-RPT~TST ✅) — SP6-DOC-01

---

## 1. 한 줄 목표

**10단계 (post-pipeline):** skeleton·verified graph → **ε-2 report**, **ε-3 verified narrative**, **ε-4 rewrite outline**.  
**코어 DAG 무변경** — analyze 완료 후 `recompose_index()` (Sprint 4 skeleton 패턴).

---

## 2. μ — SP6 재쪼개기 (5 레이어)

```
μ-RPT  ε-2 report      SP6-RPT-01~03
μ-NAR  ε-3 narrative   SP6-NAR-01~03
μ-OUT  ε-4 outline      SP6-OUT-01~02
μ-API  노출             SP6-API-01~02
μ-UI   패널             SP6-UI-01~03
μ-TST  검증             SP6-TEST-01~04
```

| μ-ID | SP6 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **RPT-01** | RPT-01 | `build_health_report(skeleton, fc)` → markdown | unit |
| **RPT-02** | RPT-02 | Gap/Strong/Weak 섹션 (C-3) | markdown contains |
| **RPT-03** | RPT-03 | NG-3 disclaimer footer | markdown |
| **NAR-01** | NAR-01 | strong chain → prose line | unit |
| **NAR-02** | NAR-02 | CAUSES only, chain len≥2 | unit |
| **NAR-03** | NAR-03 | empty → explicit placeholder | unit |
| **OUT-01** | OUT-01 | gap → `fix_gap` rewrite hint | unit |
| **OUT-02** | OUT-02 | strong outline → `keep` entries | unit |
| **API-01** | API-01 | analyze `recompose` block | pipeline_batch |
| **API-02** | API-02 | `GET /api/recompose` | server |
| **UI-01** | UI-01 | `#recompose-panel` tabs Report/Narrative/Outline | index.html |
| **UI-02** | UI-02 | analyze 완료 시 render | JS |
| **UI-03** | UI-03 | idle 시 clear | JS |
| **TST-01** | TEST-01 | fixture chain → narrative line | pytest |
| **TST-02** | TEST-02 | gap → rewrite hint | pytest |
| **TST-03** | TEST-03 | result JSON keys | pytest |
| **TST-04** | TEST-04 | sprint0~5 회귀 | pytest |

---

## 3. ε ↔ 코드 1:1 (SP6-DOC-01)

| ε (0-1) | 산출 | 코드 |
|---------|------|------|
| ε-2 | skeleton health report | `recompose/report.py` |
| ε-3 | verified narrative | `recompose/narrative.py` |
| ε-4 | rewrite outline | `recompose/outline.py` |

---

## 4. AC closure

| AC | Before | Sprint 6 |
|----|--------|----------|
| AC-REC-02 | 🔜 10단계 | ✅ recompose block + UI |
| AC-REC-01 | ✅ | ✅ pipeline still no inline rewrite |

---

## 5. NON-GOALS

- LLM full rewrite (ε-4 prose generation)  
- 코어 파이프라인 노드 추가  
- AC-REC-01 위반 (파이프라인 중간 텍스트 삽입)

---

## 6. ω — 자기 점검

| ω | 검증 |
|---|------|
| ω-1 | post-pipeline only ✅ |
| ω-2 | skeleton reuse, no duplicate Gap logic ✅ |
| ω-3 | δ disclaimer in report ✅ |
| ω-4 | sprint0~5 회귀 ✅ |

---

## 7. DoD

- [x] `tests/test_sprint6_recompose.py` PASS
- [x] sprint0~5 + stage0 PASS
- [x] Appendix H + AC-REC-02 ✅

---

## 8. 파일 맵

| 파일 | μ |
|------|---|
| `deconstructor/recompose/` | RPT, NAR, OUT |
| `deconstructor/web/pipeline_batch.py` | API-01 |
| `deconstructor/web/server.py` | API-02 |
| `web/index.html` | UI-* |
| `tests/test_sprint6_recompose.py` | TST-* |
