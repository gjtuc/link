# STAGE-1 — Cross-run corpus 영속 경계 (설계만)

> **상태:** **μ-PRE-2b-PERSIST** — 설계 문서만 (구현 **미착수**)  
> **선행:** μ-2b-02-API (`/api/status` cross_run_corpus)  
> **다음:** **μ-2b-03** — Neo4j/file 영속 구현 (별도 주문)  
> **금지:** Neo4j 코드, pipeline DAG 변경, live E2E

---

## 목적

μ-2b-00~02-API까지 **in-memory** `InMemoryCorpusStore`로 cross-run read/write 계약을 잠갔다.  
본 spec은 **영속 계층**으로 넘어가기 전 namespace·경계·마이그레이션·재시작 시나리오를 고정한다.

**관련:** [STAGE-1-CORPUS-spec.md](STAGE-1-CORPUS-spec.md) · [BRANCH-2b-spec.md](BRANCH-2b-spec.md)

---

## μ-ID

| μ-ID | 내용 | 상태 |
|------|------|------|
| **μ-PRE-2b-PERSIST** | 영속 경계 설계 + sample | ✅ (본 문서) |
| **μ-2b-03-00** | CorpusStore protocol + memory factory | `factory.py` + pytest | ✅ |
| **μ-2b-03-01** | Neo4j adapter (mock) | TBD | [ ] |
| **μ-2b-03** | 영속 store 통합 | TBD | [ ] |
| **μ-2b-02-UI** | index.html 힌트 (선택) | [ ] |

---

## batch_corpus vs cross_run vs Neo4j

| 계층 | ID / 키 | 범위 | 영속 | 코드 위치 |
|------|---------|------|------|-----------|
| **batch_corpus** | `analysis_run_id` (UUID/batch) | 단일 「전체 분석」배치 | Neo4j graph filter·session graph | `pipeline_batch.py`, `graph_filter` |
| **batch_corpus** | `merge_mode=batch_corpus` | 동일 배치 내 multi-file bridge | 배치 종료 시 소멸 (in-run pool) | `corpus_bridge.py` |
| **cross_run** | `run_id` + `session_id` | 프로세스·세션 간 fact 메타 pool | **현재:** in-memory only | `corpus/contract.py`, `ingest_hook.py` |
| **Neo4j Fact** | `fact.id` (AtomicFact UUID) | Cypher `:Fact` 노드 | bolt persist (배치별) | `weaver` / `neo4j_store` |
| **cross_run (목표)** | corpus `run_id` ≠ Neo4j `analysis_run_id` | STAGE-1 global corpus | **μ-2b-03:** MERGE 정책 별도 | TBD |

**원칙:** `analysis_run_id`는 **그래프 조회 필터**용. cross_run `run_id`는 **corpus 메타 누적**용. 1:1 동일시키지 않음 (한 session에 여러 analysis_run 가능).

---

## Namespace 규칙

| 필드 | 형식 | 발급 주체 | 유일성 |
|------|------|-----------|--------|
| `session_id` | opaque string | UI heartbeat / `LINK_SESSION_ID` / server | 프로세스·탭 세션 |
| `run_id` | UUID (현재 `batch_run_id` 재사용 가능) | `pipeline_batch` per 성공 batch | global corpus 내 unique |
| `fact_id` | AtomicFact `.id` | Deconstruct pipeline | global; corpus는 **참조만** (복제 금지) |
| `source_file` | 파일명·경로 basename | ingest C-2 | corpus 집계 키 |
| `chunk_id` | `{source_file}#chunk-k/n` | ingest | optional meta |

**금지:** corpus store에 fact 본문 duplicate — μ-2b-03도 `CorpusFactRecord` 스키마 유지.

---

## in-memory → 영속 마이그레이션 경계

| 단계 | 저장소 | 읽기 | 쓰기 |
|------|--------|------|------|
| **현재 (μ-2b-01~02-API)** | `InMemoryCorpusStore` singleton | `query.py`, `status_block.py` | `ingest_hook` (`LINK_CROSS_RUN_CORPUS=1`) |
| **μ-2b-03 (예정)** | Neo4j `:CorpusRun` / `:CorpusFactRef` 또는 JSONL sidecar | 동일 query API, store adapter | hook → adapter |
| **재시작** | in-memory **소멸** (by design) | status `enabled=true`여도 counts=0 until re-ingest | — |

**어댑터 계약:** `append_run` / `list_runs` / `facts_cross_run` 시맨틱 유지 — 구현체만 교체.

---

## MERGE·삭제·재시작 (설계)

| 시나리오 | 정책 (설계) |
|----------|-------------|
| **동일 run_id 재-append** | **거부** — `ValueError` (in-memory와 동일) |
| **동일 fact_id 다른 run** | 허용 — 최신 run_id가 canonical (query는 run 필터로 해소) |
| **Neo4j MERGE Fact** | 기존 weaver 동작 유지; corpus ref는 **별도 노드/관계** (`:CORPUS_MEMBER`) |
| **프로세스 재시작** | in-memory clear; Neo4j corpus 노드는 **유지** (μ-2b-03) — reload API 별도 |
| **session 탭 종료** | heartbeat idle → managed Neo4j stop (기존 S5); corpus in-memory는 무관 |
| **삭제** | μ-2b-03: `session_id` 단위 tombstone 또는 전체 purge — **감독 승인 후** 구현 |

---

## μ-2b-03-00 — factory (✅)

| 항목 | 내용 |
|------|------|
| Protocol | `deconstructor/corpus/store_protocol.py` — `CorpusStore` |
| Adapter | `memory_adapter.py` — `MemoryCorpusStoreAdapter` |
| Factory | `factory.py` — `LINK_CORPUS_BACKEND=memory` (default); `neo4j` → NotImplementedError |
| 소비 | `ingest_hook`, `status_block` → `get_corpus_store()` factory 경유 |

```bash
python -m pytest tests/test_stage1_corpus_store_factory.py -q
```

---

## μ-2b-03 구현 DoD (잔여)

1. `CorpusStore` protocol — `InMemoryCorpusStore` + `Neo4jCorpusStore` (또는 file)  
2. `ingest_hook` → store factory (`LINK_CORPUS_BACKEND=memory|neo4j`)  
3. 재시작 후 `summarize_corpus`가 영속 데이터 반영 (status API 동일 shape)  
4. offline pytest — mock bolt, LLM 0  
5. **금지:** `pipeline_batch` DAG 토폴로지 변경, `branch1_full_e2e` 선행 없이 live 인정  

---

## NON-GOALS

- 코어 DAG·Deconstruct 단계 순서 변경 (D-06)  
- AC-DEC-02 MUST 승격  
- `index.html` corpus UI (μ-2b-02-UI 별도)  
- live Gemini E2E  
- catalog `verified` 일괄 승격  

---

## 오프라인 검증

```bash
python -m pytest tests/test_stage1_persist_design_sample.py -q
```

**sample:** `tests/fixtures/stage1_persist_design_sample.json`
