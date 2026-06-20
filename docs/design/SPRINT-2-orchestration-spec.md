# Sprint 2 — Orchestration / Cross-Doc Bridge (G-ORC-*) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix C  
> **시나리오:** [STAGE-0-2-user-scenarios.md](STAGE-0-2-user-scenarios.md) S0-C  
> **선행:** Sprint 1 ✅ (`source_file`, `chunk_id` on AtomicFact)  
> **AC:** AC-ORC-02, 03, 04  
> **상태:** 구현 완료 (μ-POL~TST ✅) — SP2-DOC-01

---

## 1. Sprint 2 한 줄 목표

**배치 내 N 파일** ingest 후, Skeptic **CAUSES** 와 별도로 **교차 문서 bridge** 를 계산·표시하거나 **「교차 0건」** 을 명시한다. merge-only 한계(F0-C2)를 UI/API에서 투명히 드러낸다.

---

## 2. μ — SP2 재쪼개기 (5 레이어)

```
μ-POL  정책      SP2-POL-*   dedup·merge·F0-C1 회피
μ-BRG  bridge     SP2-BRG-*   corpus pool → bridge_edges
μ-MRG  merge      SP2-MRG-*   GraphFetchResult 병합 + bridge 부착
μ-UI   표시       SP2-UI-*    JSON + index.html
μ-TST  검증       SP2-TEST-*  단위·회귀
```

| μ-ID | SP2 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **POL-01** | POL-01 | Subject dedup 정책 문서 (본 문서 §4) | design |
| **POL-02** | POL-02 | F0-C1: same subject + **same** source_file ≠ bridge | test |
| **POL-03** | POL-02 | UUID merge: later wins; provenance tooltip 유지 | code comment |
| **BRG-01** | BRG-01 | `CorpusFactRef` — state → (id, subject, source_file) | unit |
| **BRG-02** | BRG-01 | `normalize_subject()` — case/space | unit |
| **BRG-03** | BRG-01 | bridge: ≥2 **distinct source_file** + same norm_subject | unit |
| **BRG-04** | BRG-01 | star topology (hub=file[0] → others), cap MAX_BRIDGE=30 | unit |
| **BRG-05** | BRG-02 | `GraphEdge.edge_kind` = `CAUSES` \| `BRIDGE` | model |
| **BRG-06** | BRG-02 | pyvis: BRIDGE = 보라 점선, tooltip 「교차 문서」 | visual |
| **MRG-01** | (batch) | `merge_graph_results` — CAUSES dedup (기존) | regression |
| **MRG-02** | (batch) | `attach_bridge_edges(fetched, states)` | integration |
| **MRG-03** | (batch) | Neo4j·세션 **둘 다** render 직전 bridge 부착 | manual |
| **UI-01** | UI-01 | API `orchestration.bridge_count` | JSON |
| **UI-02** | UI-01 | API `orchestration.merge_mode` = `batch_corpus` | JSON |
| **UI-03** | UI-01 | stats: 「교차 N건」/「교차 0건」 | index.html |
| **UI-04** | UI-01 | `items_processed>1` 일 때만 교차 라벨 | UI |
| **TST-01** | TEST-01 | 2 source_file + same subject → bridge_count≥1 | pytest |
| **TST-02** | TEST-01 | 1 file → bridge_count=0 | pytest |
| **TST-03** | TEST-01 | T-FAST + sprint0/1 regression | CI |

---

## 3. Bridge 알고리즘 (BRG-03~04) — 의사코드

```
INPUT: pipeline_states[]  (각각 completed_facts + source_document_meta)

FOR each fact IN completed_facts:
  source_file ← fact.source_file OR meta.source_file
  SKIP if not source_file or not subject
  bucket[normalize(subject)][source_file] ← one representative fact_id

FOR each bucket with |source_files| ≥ 2:
  hub ← first sorted source_file
  FOR each other file:
    EMIT BridgeEdge(hub.id → other.id)   # edge_kind=BRIDGE, NOT Skeptic CAUSES

CAP at MAX_BRIDGE_EDGES=30
```

**NOT bridge (F0-C1):**
- Same subject, **same** source_file, different UUID → 중복 노드만 (별도 bridge 없음)
- Same subject, different chunk, **same** file → bridge 없음

**IS bridge:**
- Same normalized subject, **different** source_file → 교차 후보 (S0-C C-2-3 MVP)

---

## 4. POL — Subject dedup·merge 정책 (POL-01)

| Case | 정책 | Bridge? |
|------|------|---------|
| 동일 `subject` + 다른 `source_file` | 별도 노드 유지 | ✅ 후보 |
| 동일 `subject` + 동일 file + 다른 chunk | 별도 노드 (`chunk_id`) | ❌ |
| 동일 UUID id 충돌 on merge | later run wins | — |
| LLM cross-doc 因→과 추론 | **금지** (NON-GOAL) | — |

---

## 5. API 계약 (UI-01~02)

```json
{
  "orchestration": {
    "merge_mode": "batch_corpus",
    "bridge_count": 0,
    "source_file_count": 2,
    "cross_doc_label": "교차 0건"
  }
}
```

- `bridge_count > 0` → `cross_doc_label`: 「교차 {N}건」
- `items_processed < 2` → `orchestration` 생략 또는 `bridge_count: null` (단일 파일)

---

## 6. AC closure

| AC | Before | After (Sprint 2) |
|----|--------|------------------|
| AC-ORC-02 | ❌ | ✅ bridge_count 또는 「교차 0건」 |
| AC-ORC-03 | ❌ | ✅ §4 + `corpus_bridge.py` |
| AC-ORC-04 | ⚠️ | ✅ merge_mode + F0-C2 한계 UI |

---

## 7. NON-GOALS

- LLM·Dreamer cross-doc inference
- Neo4j cross-run corpus
- Sprint 3 Deconstruct 변경
- NG-2: bridge 없이 노드 수만 증가 = 성공 아님 → **bridge_count 명시로 구분**

---

## 8. ω — 설계 자기 점검

| ω | 검증 | 결과 |
|---|------|------|
| ω-1 | Sprint 1 `source_file` 선행 (D-01) | ✅ |
| ω-2 | F0-C1 vs bridge 구분 | §4, BRG-03 |
| ω-3 | F0-C2 merge-only → UI 명시 (AC-ORC-04) | UI-03 |
| ω-4 | CAUSES vs BRIDGE 시각 구분 | BRG-06 |
| ω-5 | 단일 파일 시 bridge=0 | TST-02 |
| ω-6 | 코어 Skeptic/Weaver 무변경 | MRG-02 only post-process |

---

## 9. DoD

- [x] `tests/test_sprint2_orchestration.py` PASS
- [x] sprint0/1 + stage0 PASS
- [x] AC-ORC-02,03,04 ✅ in STAGE-0-3
- [x] STAGE-0-2 F0-C2 갱신 (한계 → Sprint 2 bridge)

---

## 10. 파일 맵

| 파일 | μ |
|------|---|
| `deconstructor/web/corpus_bridge.py` | BRG-* (신규) |
| `deconstructor/viz/neo4j_utils.py` | BRG-05 GraphEdge |
| `deconstructor/viz/state_graph.py` | MRG-01, POL-03 |
| `deconstructor/viz/visualizer.py` | BRG-06 |
| `deconstructor/web/pipeline_batch.py` | MRG-02, UI JSON |
| `web/index.html` | UI-03 |
