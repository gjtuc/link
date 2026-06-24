# Branch-SPINE — 읽기 UX (μ-SPINE-00 설계)

> **상태:** **μ-SPINE-02** ✅ — `index.py` + `main_path.py` · **μ-SPINE-02-API 착수 대기**  
> **쉬운 설명:** [BRANCH-SPINE-spec-읽기가이드.md](BRANCH-SPINE-spec-읽기가이드.md)  
> **입력:** [STAGE-0-SPINE-philosophy.md](STAGE-0-SPINE-philosophy.md) · [STAGE-0-SPINE-2-scenarios.md](STAGE-0-SPINE-2-scenarios.md) · [STAGE-0-SPINE-3-acceptance.md](STAGE-0-SPINE-3-acceptance.md)  
> **잠금:** `branch_spine_unlocked=true` — **μ-SPINE-UNLOCK** ✅ (2026-06-24)

---

## 1차 목표

**SPINE** = 0-SPINE 철학의 **읽기 레이어**: `link_sentence` / `link_mechanism`, spine index, 좌측 목록·옆 패널·hover/click.

| 항목 | 내용 |
|------|------|
| 범위 | post-pipeline **표현·읽기** — Deconstruct/Skeptic **순서 변경 없음** |
| 1차 ω | C-SPINE MUST 묶음 (05+01+09+02+08) |
| 2차 | BUNDLE, CHUNK, density, follow H, R6 full |

---

## 선행 (DoD before μ-SPINE-01)

| # | 조건 | 상태 |
|---|------|------|
| 1 | STAGE-0-SPINE-1~3 문서 **승인** | ✅ 완료본 |
| 2 | μ-SPINE-00 offline 검증 | ✅ `spine_design_sample.json` + pytest |
| 3 | Branch-0 회귀 유지 | MUST (구현 μ마다) |
| 4 | `branch_spine_unlocked=true` | ✅ **μ-SPINE-UNLOCK** (2026-06-24) |

### μ-SPINE-00 산출 (완료)

| 산출 | 경로 |
|------|------|
| design sample | `tests/fixtures/spine_design_sample.json` |
| pytest | `tests/test_spine_design_sample.py` |
| contract 예시 | sample 내 `contract_sample` (S-SPINE-A) |

---

## 데이터 계약

### LinkRationale (edge)

```python
# deconstructor/spine/contract.py (예정)
@dataclass
class LinkRationale:
    source_fact_id: str
    target_fact_id: str
    edge_kind: str  # CAUSES | BRIDGE
    link_sentence: str      # R4 — hover line 2
    link_mechanism: str     # R6 — panel body (CAUSES only)
    locale: str             # ko | en — §1d-9
```

**생성:** μ-SPINE-01 — Skeptic/weaver **이후**, 배치 병합 **이전** 또는 병합 후 edge list 순회.

**폴백:** §1d-8 기계 조합; `link_mechanism=""` for BRIDGE.

### SpineRecord

```python
@dataclass
class SpineRecord:
    spine_id: str           # stable per analyze run
    index: int              # 1-based display 「뼈대 N」
    label: str              # 「원료 → 수율」
    bridge_count: int
    node_ids: list[str]
    edge_ids: list[tuple[str,str]]  # (source, target)
    main_path_node_ids: list[str]   # §1f-1f-2
    is_branched: bool
```

**생성:** μ-SPINE-02 — `spine_index.py` from merged graph + `find_strong_chains` 확장 (BRIDGE, DAG).

### Analyze API 확장

```json
{
  "spine": {
    "spines": [ SpineRecord... ],
    "selected_spine_id": "...",
    "filters": { "include_hypothesis": false, "include_bridge": true }
  },
  "link_rationales": [ LinkRationale... ]
}
```

기존 `skeleton` **유지** (§7).

---

## UI 와이어 (텍스트)

```
┌─────────────────────────────────────────────────────────┐
│ [뼈대 목록]          │  [인과 그래프 — dim 비선택]      │
│ ▶ 뼈대 1 · A → B     │                                  │
│   뼈대 2 · … (교차1) │                                  │
│ [가설 포함] [교차✓]  │                                  │
├──────────────────────┤                                  │
│ [팩트 상세 | 인과 상세]                                  │
│ (토글 패널)          │                                  │
│ [다른 업로드 문서도 참고]                                │
│ [이 인과에 대해 더 물어보기____________]                 │
└─────────────────────────────────────────────────────────┘
```

- 그래프: vis — edge `title` = R4 2줄; node `title` 제거 → click → postMessage 패널.
- §1d-1: `tooltipDelay: 120`, drag 시 tooltip off.

---

## μ-ID (설계안)

| μ-ID | 내용 | 검증 | 상태 |
|------|------|------|------|
| **μ-SPINE-00** | 본 spec + offline sample JSON | `test_spine_design_sample.py` | ✅ |
| **μ-SPINE-UNLOCK** | `branch_spine_unlocked=true` (감독 승인·sample 갱신) | branch_state gate | ✅ |
| **μ-SPINE-01** | `contract.py` + `rationale.py` 생성 | unit + fixture | ✅ 2026-06-24 |
| **μ-SPINE-02** | `spine_index.py` (DAG, BRIDGE, main_path) | unit | ✅ 2026-06-24 |
| **μ-SPINE-02-API** | analyze JSON `spine`, `link_rationales` | API test | [ ] |
| **μ-SPINE-03-UI** | 좌측 목록 + dim + hover R4 | E2E A | [ ] |
| **μ-SPINE-04-UI** | 옆 패널 노드/링크 토글 | E2E F, E | [ ] |
| **μ-SPINE-05-UI** | 5b-B 체크 + NG-3 | E2E E | [ ] |
| **μ-SPINE-ω** | closure fixtures A~D + MUST AC | `test_spine_closure.py` | [ ] |
| **μ-SPINE-BUNDLE** | §10 TopicBundle | C-BUNDLE | [ ] 2차 |
| **μ-CHUNK-STRUCT** | §6 절·문단 청크 | C-CHUNK | [ ] 별도 |

---

## 모듈 (예정)

| 경로 | 역할 |
|------|------|
| `deconstructor/spine/contract.py` | LinkRationale, SpineRecord |
| `deconstructor/spine/rationale.py` | R4/R6 mechanical fallback |
| `deconstructor/spine/index.py` | spine enumeration |
| `deconstructor/spine/main_path.py` | DAG 주 경로 |
| `web/index.html` | 목록·패널·필터 |
| `deconstructor/viz/visualizer.py` | edge title = R4; node title off |
| `deconstructor/viz/legend.py` | 발견성 copy |

**금지 (μ-SPINE-01 전):** `index.html` spine 패널 대규모 착수 without contract freeze.

---

## 알고리즘 메모 (μ-SPINE-02)

1. `merge_graph_results` 후 `GraphNode`/`GraphEdge` 입력.
2. CAUSES edges → 기존 `find_strong_chains` 후보 (min_edges=2).
3. BRIDGE edges로 후보 path **연장** (§1f-1b); CAUSES≥1 필터.
4. 분기 허용 → spine = **DAG**; `main_path` = longest CAUSES-only path (tie: 더 많은 CAUSES).
5. 정렬: `(-len(main_path), -causes_ratio)`; cap 20 + 더 보기.
6. `bridge_count` = spine 내 BRIDGE edges.

---

## NON-GOALS (구현 시)

- Neo4j 스키마 변경 (1차) — session JSON 우선.
- force graph 제거.
- 저자 목차 순 자동 spine.
- BRIDGE만 spine.

---

## Worker 검증 (ω 블록)

| ID | 내용 |
|----|------|
| W1 | `pytest tests/test_spine_*` |
| W2 | fixture A B C D |
| W3 | 모듈 헤더 STAGE 0-SPINE 3~8줄 |
| W4 | 본 spec AC 표와 테스트 1:1 |
| W5 | commit hash |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-22 | μ-SPINE-00 초안 |
| 2026-06-22 | μ-SPINE-00 완료 — spine_design_sample + pytest |
