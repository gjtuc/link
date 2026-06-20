# S0-A E2E 기록 — 논문 PDF 1편

> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) § S0-A  
> **실행:** `python scripts/s0a_e2e_run.py`  
> **픽스처:** `tests/fixtures/s0a_paper.pdf` (`python scripts/generate_s0a_fixture.py`)

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-06-20 |
| OS | Windows 10 (cp949 콘솔) |
| 분기 | Sprint 0~7 완료 후 |
| Neo4j | 로컬 bolt (파이프라인 자동 기동) |
| Fact-Checker | `corpus` (Tavily 미사용 시 document-internal) |

---

## A-2 체크리스트 (관측값)

| ID | 결과 | 관측 |
|----|------|------|
| A-2-1 ingest, 요약 없음 | ✅ | sources=1, extracted_chars≈1673, document_page_count=4 |
| A-2-2 파이프라인 완료 | ✅ | `ok=true`, completed_facts_total=12 |
| A-2-3 그래프 | ✅ | nodes=17, edges=32 (pyvis + provenance) |
| A-2-4 FC 모드 | ✅ | `fact_checker.mode=corpus` |
| A-2-5 Gap/Strong (NG-2) | ✅ | gap_count=6, strong_chain_count=50, recompose report 존재 |
| partial_run | ✅ | `has_partial_run=false`, `failed_step=null` |

---

## 파이프라인 요약

- Deconstruct → 12 atomic facts (4-page PDF fixture)
- Dreamer → 5 inferred hypotheses
- Corpus FC → 5 promoted
- Skeptic → 32 CAUSES edges
- Post-pipeline: skeleton index, recompose ε-2~4, watch/guards

---

## 이슈·수정

1. **UnicodeEncodeError (cp949):** `provenance/viz_style.py` `_log()` 및 `scripts/s0a_e2e_run.py` 출력을 `safe_print`로 교체.
2. **A-2-2 β-2:** 청크당 fact 수는 여전히 개선 여지 (Sprint 3 휴리스틱; non-atomic 재귀는 후속).

---

## 판정

**S0-A PASS** — P0 ingest·파이프라인·corpus FC·skeleton/recompose/watch AC 충족.
