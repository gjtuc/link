# STAGE-1 — Cross-run corpus 계약

> **상태:** μ-2b-00 (skeleton)  
> **선행:** μ-UNLOCK-2b (`branch_2b_unlocked=true`)  
> **다음:** μ-2b-01 — cross-run ingest (pipeline·Neo4j 경계)  
> **금지:** 코어 DAG 토폴로지 변경, live Gemini E2E, `batch_corpus` 동작 변경

---

## 목적

Branch-2b **STAGE 1** — 단일 batch(`merge_mode=batch_corpus`)를 넘어 **세션·런 간** fact pool을 누적·조회하는 계약을 정의한다.

| 범위 | μ-2b-00 (본) | μ-2b-01 (다음) |
|------|----------------|----------------|
| 계약·타입 | ✅ `deconstructor/corpus/contract.py` | ingest hook |
| 저장소 스켈레ton | ✅ `memory_store.py` (in-process) | Neo4j·파일 영속 |
| pipeline_batch | **미연결** | cross-run append |
| UI/API | — | μ-2b-02 |

**0단계와의 관계:** Sprint 2 `batch_corpus` + `corpus_bridge` = **단일 런** 내 교차. STAGE-1 = **런 간** global corpus.

---

## μ-ID

| μ-ID | 내용 | 검증 |
|------|------|------|
| **μ-2b-00** | corpus 계약 + in-memory store | `tests/test_stage1_corpus_contract.py` |
| **μ-2b-01** | cross-run ingest | TBD |
| **μ-2b-02** | corpus query / UI | TBD |
| **μ-2b-ω** | 2b 1차 마감 | sample + baseline |

---

## 계약 (contract.py)

### CorpusScope

| 값 | 의미 |
|----|------|
| `batch_corpus` | 단일 pipeline batch (Branch-1, 기존) |
| `cross_run` | STAGE-1 global pool — 런 간 누적 |

### CorpusRunRecord (필수 필드)

| 필드 | 타입 | 설명 |
|------|------|------|
| `run_id` | str | UUID 또는 monotonic id |
| `session_id` | str | UI/서버 세션 |
| `merge_mode` | str | `batch_corpus` \| `cross_run` |
| `source_files` | list[str] | distinct source_file |
| `fact_count` | int | ≥0 |
| `created_at` | str | ISO8601 |

### CorpusFactRecord (필수 필드)

| 필드 | 타입 | 설명 |
|------|------|------|
| `fact_id` | str | AtomicFact id |
| `subject` | str | 비어 있지 않음 |
| `source_file` | str | C-2 provenance |
| `chunk_id` | str | optional meta |
| `run_id` | str | 소속 run |

**검증:** `validate_run_record`, `validate_fact_record` — MUST 필드·scope enum.

---

## memory_store.py (skeleton)

`InMemoryCorpusStore` — 프로세스 내 dict/list; **Neo4j·disk 없음**.

| 메서드 | 동작 |
|--------|------|
| `append_run(run, facts)` | run + facts 원자적 추가 |
| `list_runs()` | run_id 순 |
| `facts_for_run(run_id)` | 단일 run |
| `facts_cross_run()` | 전 run 합집합 |
| `distinct_source_files()` | global distinct |
| `clear()` | 테스트용 |

---

## NON-GOALS (μ-2b-00)

- `pipeline_batch.py` DAG 변경  
- Neo4j MERGE / cross-run sync  
- Fact-Checker corpus pool 교체  
- AC-DEC-02 MUST 승격  

---

## 실행

```bash
python -m pytest tests/test_stage1_corpus_contract.py -q
python scripts/stage0_reaudit_baseline.py
python scripts/phase_r_regression.py
```

**관련:** [BRANCH-2b-spec.md](BRANCH-2b-spec.md) · [STAGE-0-CLOSURE-ROADMAP.md](STAGE-0-CLOSURE-ROADMAP.md)
