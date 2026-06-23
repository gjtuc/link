# STAGE-1 — Cross-run corpus 계약

> **상태:** μ-2b-02-R (READ 계약)  
> **선행:** μ-2b-01 (`ingest_hook`)  
> **다음:** μ-2b-02-API — `/api/status` corpus 힌트  
> **금지:** 코어 DAG 토폴로지 변경, live Gemini E2E, `batch_corpus` 동작 변경

---

## 목적

Branch-2b **STAGE 1** — 단일 batch(`merge_mode=batch_corpus`)를 넘어 **세션·런 간** fact pool을 누적·조회하는 계약을 정의한다.

| 범위 | μ-2b-00 (본) | μ-2b-01 (다음) |
|------|----------------|----------------|
| 계약·타입 | ✅ `deconstructor/corpus/contract.py` | ingest hook |
| 저장소 스켈레ton | ✅ `memory_store.py` (in-process) | ✅ ingest hook (μ-2b-01) |
| pipeline_batch | read-only hook (`LINK_CROSS_RUN_CORPUS`) | Neo4j 영속 |
| UI/API | — | μ-2b-02-API |

**0단계와의 관계:** Sprint 2 `batch_corpus` + `corpus_bridge` = **단일 런** 내 교차. STAGE-1 = **런 간** global corpus.

---

## μ-ID

| μ-ID | 내용 | 검증 |
|------|------|------|
| **μ-2b-00** | corpus 계약 + in-memory store | `tests/test_stage1_corpus_contract.py` |
| **μ-2b-01** | cross-run ingest hook | `tests/test_stage1_corpus_ingest.py` |
| **μ-2b-02-R** | corpus READ/query 계약 | `tests/test_stage1_corpus_query.py` |
| **μ-2b-02-API** | `/api/status` corpus 힌트 | `tests/test_stage1_corpus_status_api.py` |
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

## μ-2b-01 — cross-run ingest hook

**모듈:** `deconstructor/corpus/ingest_hook.py`  
**연결:** `pipeline_batch.py` — pipeline `ok` 후 `maybe_append_batch_corpus` (side-effect only)

### 환경 변수

| env | 기본 | 동작 |
|-----|------|------|
| `LINK_CROSS_RUN_CORPUS` | off (`0`) | `1`/`true`/`yes` 시 성공 batch를 global store에 append |
| `LINK_SESSION_ID` | — | optional; 없으면 `batch_run_id` 사용 |

### 동작

1. `pipeline_states` → `CorpusFactRecord` (subject + source_file 필수)
2. `merge_mode=cross_run` `CorpusRunRecord` 생성
3. `InMemoryCorpusStore.append_run` (프로세스 싱글톤)
4. `orchestration.corpus_scope=cross_run` 힌트 (multi-file 시, `merge_mode`는 `batch_corpus` 유지)
5. hook 실패·검증 실패 → **pipeline 결과 불변**

```bash
python -m pytest tests/test_stage1_corpus_ingest.py tests/test_stage1_corpus_contract.py -q
```

---

## READ 계약 (μ-2b-02-R)

**모듈:** `deconstructor/corpus/query.py`

| 함수 | 동작 |
|------|------|
| `query_runs(store, session_id=None)` | run 목록; `session_id` optional |
| `query_facts(store, session_id=, run_id=, subject_contains=)` | fact 필터 (AND); 빈 store → `[]` |
| `summarize_corpus(store, session_id=None)` | `CorpusQuerySummary` — run/fact count, source_files |

**빈 store:** `run_count=0`, `fact_count=0`, `source_files=[]`.

**검증:** 빈 `session_id`/`run_id` 문자열 → `ValueError`.

```bash
python -m pytest tests/test_stage1_corpus_query.py -q
```

**sample:** `tests/fixtures/stage1_corpus_query_sample.json`

---

## API status (μ-2b-02-API)

**모듈:** `deconstructor/corpus/status_block.py`  
**엔드포인트:** `GET /api/status` → `"cross_run_corpus"` 블록 (기존 키 유지)

| 필드 | 설명 |
|------|------|
| `enabled` | `LINK_CROSS_RUN_CORPUS` on 여부 |
| `run_count` | `summarize_corpus` |
| `fact_count` | 동일 |
| `source_files` | distinct source_file |
| `session_id` | 필터 적용 시 (`LINK_SESSION_ID` 또는 인자) |

`enabled=false` 시 counts 0, `source_files=[]` 고정.

```bash
python -m pytest tests/test_stage1_corpus_status_api.py -q
```

---

## NON-GOALS (μ-2b-00~02-API)

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
