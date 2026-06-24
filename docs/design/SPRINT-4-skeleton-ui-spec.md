# Sprint 4 — Skeleton Index + UI (G-SKP-INDEX, G-UI-SKELETON) 상세 설계

> **상위:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) Appendix E  
> **AC:** AC-SKP-03,04,05 · AC-UI-04,05  
> **선행:** Sprint 3 ✅ (completed graph)  
> **상태:** 구현 완료 (μ-IDX~TST ✅) — SP4-DOC-01

---

## 1. 한 줄 목표

**C-3, NG-4:** 파이프라인 **완료 그래프**에서 Gap/Strong/Weak **skeleton index** 를 계산하고, force graph와 **병행**해 Outline·Skeleton Health 패널로 표시한다.  
**코어 DAG·Weaver/Skeptic 무변경** (D-03, D-06).

---

## 2. μ — SP4 재쪼개기 (5 레이어)

```
μ-IDX  지표 규칙   SP4-IDX-01~03
μ-OUT  Outline    SP4-IDX-04
μ-API  노출        SP4-API-01
μ-UI   패널        SP4-UI-01~03
μ-TST  검증        SP4-TEST-01
```

| μ-ID | SP4 | 설명 | 합격 관측 |
|------|-----|------|-----------|
| **IDX-01** | IDX-01 | `skeleton_index(nodes, edges) -> dict` | unit import |
| **IDX-02** | IDX-02 | Gap: CAUSES in-deg 0 ∧ conclusion-like | fixture gap=2 |
| **IDX-03** | IDX-03 | Strong: CAUSES simple path ≥2 edges | fixture chain=1 |
| **IDX-04** | IDX-01 | Weak: promoted inferred ∪ orphan extracted (strong·gap 제외) | unit |
| **IDX-05** | IDX-01 | BRIDGE 엣지는 Gap/Strong **제외**, outline 참조만 | unit |
| **OUT-01** | IDX-04 | `outline[]`: id, subject, state_change, role, depth | JSON field |
| **OUT-02** | IDX-04 | role ∈ gap \| strong \| weak \| other | enum test |
| **API-01** | API-01 | analyze result에 `skeleton` block | pipeline_batch |
| **API-02** | API-01 | `GET /api/skeleton` → last analyze skeleton | server 200 |
| **UI-01** | UI-01 | `#skeleton-health` Gap/Strong/Weak counts | index.html |
| **UI-02** | UI-01 | `#skeleton-outline` claim list (role badge) | index.html |
| **UI-03** | UI-03 | outline click → postMessage highlight | legend listener |
| **TST-01** | TEST-01 | known graph → exact counts | pytest |
| **TST-02** | TEST-01 | empty graph → zeros | pytest |
| **TST-03** | TEST-01 | API wiring in result dict keys | pytest |

---

## 3. γ ↔ 코드 1:1 (SP4-DOC-01)

| γ (0-1) | 데이터 조건 | 코드 |
|---------|-------------|------|
| 빈 원인 (Gap) | conclusion-like fact, CAUSES in-edge 0 | `rules.find_gaps` |
| Strong 원인→결과 | verified CAUSES path length ≥2 | `rules.find_strong_chains` |
| Weak | promoted inferred 또는 CAUSES 미연결 extracted (gap·strong 제외) | `rules.find_weak` |
| 원인→결과 검증 | `edge_kind==CAUSES` | Strong/Gap 집계에만 사용 |
| 교차 bridge | `edge_kind==BRIDGE` | outline depth 계산 제외 |

### conclusion-like 휴리스틱 (IDX-02)

CAUSES 기준 차수 `in_d`, `out_d`:

1. `out_d > 0` — downstream 원인 주장이지만 upstream 없음 → Gap 후보  
2. `state_change` 에 결과 키워드 (`increased`, `decreased`, `rose`, `fell`, `result`, `achieved`, `improved`, `reduced`, `상승`, `하락`, `증가`, `감소`)  
3. `out_d == 0` — leaf(과) 노드

**Gap** = conclusion-like ∧ `in_d == 0` (CAUSES only)

---

## 4. Strong chain (IDX-03)

- **CAUSES** 엣지만 사용 (`edge_kind == "CAUSES"`)  
- **chain**: 노드 id 순서, **연속 CAUSES** ≥2 edges (노드 ≥3)  
- **strong_chain_count**: 서로 다른 chain tuple 수 (max 50 cap — UI 폭주 방지)  
- AC-SKP-04: fixture `A→B→C` → count ≥1

---

## 5. Outline (OUT-*)

- CAUSES DAG에서 in-deg 0 노드를 root로 BFS depth  
- Gap 노드는 role=`gap`, strong chain 소속은 role=`strong`  
- 동일 depth 내 subject 사전순  
- BRIDGE는 outline 항목에 `(bridge)` 표시 없음 — **NON-GOAL** Sprint 4

---

## 6. API shape (API-01)

```json
{
  "skeleton": {
    "gap_count": 1,
    "strong_chain_count": 1,
    "weak_count": 0,
    "gaps": [{"id", "subject", "state_change", "reason"}],
    "strong_chains": [{"node_ids": [], "labels": [], "length": 2}],
    "weak": [{"id", "subject", "state_change", "reason"}],
    "outline": [{"id", "subject", "state_change", "role", "depth", "parent_id"}],
    "health_summary": {"gap_count", "strong_chain_count", "weak_count", "node_count", "causes_edge_count"}
  }
}
```

---

## 7. AC closure

| AC | Before | Sprint 4 |
|----|--------|----------|
| AC-SKP-03 | ❌ | ✅ gap_count in skeleton |
| AC-SKP-04 | ❌ | ✅ strong_chain_count ≥1 (fixture) |
| AC-SKP-05 | ⚠️ 수동 | ✅ SKP-03/04로 판정 (0-4 갱신) |
| AC-UI-04 | ❌ | ✅ #skeleton-outline |
| AC-UI-05 | ❌ | ✅ #skeleton-health |

---

## 8. ω — 설계 자기 점검

| ω | 검증 |
|---|------|
| ω-1 | builder/weaver/skeptic 무변경 ✅ |
| ω-2 | G-SKP-INDEX 선행 G-UI-SKELETON (D-03) ✅ |
| ω-3 | γ Gap/Strong/Weak ↔ rules.py 1:1 ✅ |
| ω-4 | force graph 유지, 패널 추가만 (NON-GOALS) ✅ |
| ω-5 | Sprint 0~3 회귀 pytest ✅ |

---

## 9. DoD

- [x] `tests/test_sprint4_skeleton.py` PASS
- [x] sprint0~3 + stage0 PASS
- [x] 0-3 AC-SKP-03,04,05 · AC-UI-04,05 ✅
- [x] Appendix E 완료본 + PROCESS Sprint 4 ✅

---

## 10. 파일 맵

| 파일 | μ |
|------|---|
| `deconstructor/skeleton/rules.py` | IDX-02,03,04,05 |
| `deconstructor/skeleton/index.py` | IDX-01, OUT-* |
| `deconstructor/web/pipeline_batch.py` | API-01 |
| `deconstructor/web/server.py` | API-02 |
| `web/index.html` | UI-* |
| `deconstructor/viz/legend.py` | UI-03 highlight |
| `tests/test_sprint4_skeleton.py` | TST-* |
