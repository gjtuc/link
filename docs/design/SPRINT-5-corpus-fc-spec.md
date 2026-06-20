# Sprint 5 — Corpus Fact-Checker (G-FC-CORPUS) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix G  
> **AC:** AC-FC-02 full, AC-FC-05  
> **선행:** Sprint 1 ✅ (provenance pool), Sprint 2 ✅ (normalize_subject)  
> **상태:** 구현 완료 (μ-CFG~TST ✅) — SP5-DOC-01

---

## 1. 한 줄 목표

**TAVILY_DISABLED** 논문·보고서 모드에서 Dreamer 가설을 **웹 대신 문서 corpus**(extracted `completed_facts` 풀)로 promote/drop.  
UI는 stub 「미검증」 대신 **「문서 내부 검증」** 표시 (AC-FC-02 full).  
**코어 DAG 토폴로지 불변** — fact_checker 노드 내부 경로만 확장.

---

## 2. μ — SP5 재쪼개기 (6 레이어)

```
μ-CFG  설정       SP5-CFG-01~02
μ-POOL corpus 풀  SP5-POOL-01~03
μ-MAT  매칭 규칙  SP5-MAT-01~04
μ-NODE 노드 경로  SP5-NODE-01~02
μ-API  배치·UI   SP5-API-01~03
μ-TST  검증      SP5-TEST-01~04
```

| μ-ID | SP5 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **CFG-01** | CFG-01 | `CORPUS_FC_ENABLED` (default True) | config |
| **CFG-02** | CFG-01 | `resolve_fact_checker_mode()` → live\|corpus\|stub | unit |
| **POOL-01** | POOL-01 | `collect_corpus_pool(state)` = batch pool + completed | unit |
| **POOL-02** | POOL-02 | batch: 이전 run `completed_facts` 누적 전달 | pipeline_batch |
| **POOL-03** | POOL-01 | pool = extracted atomic only (inferred 제외) | unit |
| **MAT-01** | MAT-01 | norm_subject exact / substring match → promote | unit |
| **MAT-02** | MAT-02 | token overlap ≥0.5 + state 공유 → promote | unit |
| **MAT-03** | MAT-03 | `anchor_fact_id` in pool → promote | unit |
| **MAT-04** | MAT-04 | no match → drop (δ: 출처 명시) | unit |
| **NODE-01** | NODE-01 | `fact_checker_node(..., mode=corpus)` | integration |
| **NODE-02** | NODE-02 | live/stub/corpus 3-way, Tavily 0 when corpus | log |
| **API-01** | API-01 | analyze JSON `fact_checker.mode` + pool stats | pipeline_batch |
| **API-02** | API-02 | `/api/status` fact_checker=corpus | server |
| **API-03** | API-03 | index 「문서 내부 검증」 badge + fc-hint | index.html |
| **TST-01** | TEST-01 | match promote / no-match drop | pytest |
| **TST-02** | TEST-02 | mode=corpus when TAVILY_DISABLED | pytest |
| **TST-03** | TEST-03 | batch pool accum cross-source | pytest |
| **TST-04** | TEST-04 | sprint0~4 회귀 | pytest |

---

## 3. AC closure

| AC | Before | Sprint 5 |
|----|--------|----------|
| AC-FC-02 | ✅ stub UI only | ✅ corpus → 「문서 내부 검증」 |
| AC-FC-05 | 🔜 | ✅ live → 「웹 검색 검증」(Sprint 0 + 명시) |
| AC-FC-04 | ✅ Tavily 0 | ✅ corpus 경로 Tavily 0 유지 |

---

## 4. γ·δ 정합

- **promoted** with corpus reason in `reasoning` — δ: 검증 출처 숨기지 않음  
- corpus ≠ 진실 보장 (NG-3) — UI hint 유지  
- **NON-GOAL:** LLM corpus verifier (Sprint 5는 규칙 매칭만)

---

## 5. ω — 설계 자기 점검

| ω | 검증 |
|---|------|
| ω-1 | builder 노드 순서 무변경 ✅ |
| ω-2 | Tavily disabled + corpus → 0 web calls ✅ |
| ω-3 | Sprint 2 `normalize_subject` 재사용 ✅ |
| ω-4 | `fact_checker_dry_run=True` 테스트 → stub 유지 ✅ |

---

## 6. DoD

- [x] `tests/test_sprint5_corpus_fc.py` PASS
- [x] sprint0~4 + stage0 PASS
- [x] Appendix G + 0-3 AC 갱신

---

## 7. 파일 맵

| 파일 | μ |
|------|---|
| `deconstructor/config.py` | CFG-* |
| `deconstructor/agents/fact_checker/corpus.py` | POOL-*, MAT-* |
| `deconstructor/agents/fact_checker/node.py` | NODE-* |
| `deconstructor/pipeline/state.py` | POOL-02 |
| `deconstructor/web/pipeline_batch.py` | POOL-02, API-01 |
| `deconstructor/web/pipeline_link.py` | POOL-02 |
| `deconstructor/graph/builder.py` | NODE-01 |
| `web/index.html` | API-03 |
| `tests/test_sprint5_corpus_fc.py` | TST-* |
