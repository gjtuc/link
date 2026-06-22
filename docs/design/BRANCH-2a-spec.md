# Branch-2a — μ-A 깊이 (AC-DEC-02 밀도 관측)

> **상태:** 착수 (unlock 후)  
> **선행:** μ-PROBE-01~03, `unlock_branch2.py`  
> **잠금 유지:** Branch-2b (STAGE-1), Branch-3 (μ-R edge)

---

## 1차 목표 (쪼개기 — 구현은 다음 μ)

| μ-ID | 내용 | 검증 |
|------|------|------|
| **μ-B2a-01** | AC-DEC-02 median 관측 E2E | `scripts/b2a_density_observe_e2e.py` (다음 μ) |
| **μ-B2a-02** | probe → capabilities evidence | `catalog.py` — 2026-06-22 갱신 |
| **μ-B2a-03** | ROADMAP Branch-2a 행 | `STAGE-0-CLOSURE-ROADMAP.md` + baseline |

---

## 선행 (Phase 1)

- `cat-neo4j-off`, `cat-pdf-triple`, `cat-scanned-pdf` probe logs
- [CAPABILITY-PROBE-spec.md](CAPABILITY-PROBE-spec.md)

---

## NON-GOALS

- Branch-2b / STAGE-1
- Branch-3 / μ-R edge 확장
- 코어 DAG 토폴로지 변경

---

## 실행 (다음 μ)

```bash
python scripts/b2a_density_observe_e2e.py  # TODO — stub only
```
