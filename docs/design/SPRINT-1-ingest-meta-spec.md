# Sprint 1 — Ingest Meta (G-ING-META) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix B  
> **AC:** AC-ING-05 (C-2)  
> **상태:** 구현 완료 (μ-L0~L3 ✅) — SP1-DOC-01

---

## μ — SP1-META 재쪼개기 (4 레이어)

```
μ-L0  스키마     P-01~03  AtomicFact 필드, chunk_id 규칙
μ-L1  ingest     I-01~04  ExtractedSource → expand_document_sources
μ-L2  pipeline   L-01~04  State → verify stamp
μ-L3  관측       V-01~03  debug, tooltip, Neo4j
```

| μ-ID | SP1 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **P-01** | META-06 | `AtomicFact.source_file/page_range/chunk_id` | model fields |
| **P-02** | META-01 | `ExtractedSource` 동일 필드 + index/total | dataclass |
| **P-03** | META-02 | `make_chunk_id(file, i, n)` | unit test |
| **I-01** | META-02 | `expand_document_sources(source_file=…)` | 2 chunks → 2 ids |
| **I-02** | META-02 | PDF `page_range` = `p.*` suffix | page label |
| **I-03** | META-02 | `document_sources_from_bytes` → file name | filename |
| **L-01** | META-04 | `State.source_document_meta` | state key |
| **L-02** | META-03 | `make_initial_state(source_document_meta=)` | factory |
| **L-03** | META-03 | `run_pipeline_with_steps` 전달 | pipeline_link |
| **L-04** | META-05 | `tag_as_extracted(..., document_meta=)` | verify node |
| **V-01** | META-08 | `_fact_brief` + chunk 집계 | debug JSON |
| **V-02** | META-07 | GraphNode + pyvis tooltip | tooltip text |
| **V-03** | META-07 | Neo4j MERGE + fetch | optional DB |

---

## chunk_id 규칙 (P-03)

```
{safe_filename}#chunk-{index}/{total}
```

- `safe_filename`: `#`, `/` → `_`
- `source_file`: 업로드 파일명 또는 ingest label (URL·텍스트 블록 id)
- `page_range`: PDF 청크만 `p.1` / `p.1-3` (suffix에서 추출)

---

## 데이터 흐름

```
document_sources_from_bytes
  → expand_document_sources (메타 채움)
  → ExtractedSource
  → pipeline_batch → source_document_meta dict
  → make_initial_state
  → verify_node → tag_as_extracted → AtomicFact.meta
  → debug / pyvis / Neo4j
```

---

## NON-GOALS (Sprint 1)

- Dreamer promoted에 anchor provenance 복사 (Sprint 2+)
- cross-doc bridge
- LLM 프롬프트 변경

---

## DoD

- [x] `tests/test_sprint1_ingest_meta.py` PASS
- [x] `test_stage0_acceptance.py` PASS
- [x] AC-ING-05 ✅ in STAGE-0-3
