# Capability catalog probes (live)

> **상태:** μ-PROBE Phase 1  
> **선행:** Q3 `aa9b243`, `stage0_reaudit_baseline` exit 0  
> **스크립트:** `scripts/capability_catalog_probe.py`

---

## μ-ID

| μ-ID | 내용 | 실행 |
|------|------|------|
| **μ-PROBE-00** | 공통 probe 스크립트 + detail JSON | `capability_catalog_probe.py` |
| **μ-PROBE-01** | `cat-neo4j-off` | `neo4j-off` |
| **μ-PROBE-02** | `cat-pdf-triple` | `pdf-triple` |
| **μ-PROBE-03** | `cat-scanned-pdf` | `scanned-pdf [--path]` |

**관측 (2026-06-22):**

| cat-id | exit | pipeline_ok | 비고 |
|--------|------|-------------|------|
| `cat-neo4j-off` | 0 | true | bolt offline, ~292s; `LINK_DISABLE_NEO4J_AUTO_START` 권장 |
| `cat-pdf-triple` | 0 | true | 3 source_file, ~496s |
| `cat-scanned-pdf` | 2 | — | `not_true_scan` (스캔 PDF 없음), log·detail 필수 |

---

## neo4j-off

- **방법:** `NEO4J_URI=bolt://127.0.0.1:19999` (bolt 불가)
- **입력:** `tests/fixtures/s0b_draft_short.txt` 1건
- **합격:** Phase R ok + `pipeline_ok=true`

---

## pdf-triple

- **입력:** `s0a_paper.pdf` → `file-a/b/c.pdf` (동일 내용 3파일)
- **합격:** `distinct_source_file` 3 + pipeline ok

---

## scanned-pdf

- 우선순위: fixtures `*scan*.pdf` → Desktop/KCH 탐색 → `not_true_scan` fallback exit 2

---

## 산출

| 경로 | 내용 |
|------|------|
| `logs/capability_runs/YYYYMMDD-HHMM-<cat-id>.json` | `log_capability_run.py` |
| `logs/capability_probes/YYYYMMDD-HHMM-<cat-id>-detail.json` | checklist·neo4j·files·pipeline_ok |

관련: [Q2-CAPABILITIES-spec.md](Q2-CAPABILITIES-spec.md), [BRANCH-2a-spec.md](BRANCH-2a-spec.md)
