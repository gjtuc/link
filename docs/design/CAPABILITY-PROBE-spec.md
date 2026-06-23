# Capability catalog probes (live)

> **상태:** μ-PROBE Phase 1 + ω 재진입 (S5·R1)  
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
| **μ-PROBE-S5** | Neo4j S5 auto-start skip 계약 | `LINK_DISABLE_NEO4J_AUTO_START` + pytest |
| **μ-PROBE-R1** | neo4j-off 재실행 (S5 적용) | `neo4j-off` 1회 |
| **μ-PROBE-SCAN-ω** | born-digital PDF 503 관측 (catalog 무변경) | spec + sample only |

---

## LINK_DISABLE_NEO4J_AUTO_START (μ-PROBE-S5)

**목적:** bolt 불가 probe 시 S5 ``ensure_neo4j_running``(Desktop 기동·최대 90s) 생략.

| 항목 | 값 |
|------|-----|
| env | `LINK_DISABLE_NEO4J_AUTO_START=1` (`true`/`yes` 동일) |
| 설정 주체 | `capability_catalog_probe.py neo4j-off` (cmd 진입 시) |
| 코드 | `deconstructor/web/pipeline_batch.py` → `_ensure_neo4j_tracked` |
| tracker | `S5-NEO4J-ENSURE` skip — `auto-start disabled (probe)` |
| pytest | `tests/test_pipeline_neo4j_probe_skip.py` |

**배치 공통:** probe 외 스크립트도 동일 env 로 S5 스킵 가능 (세션 그래프·HTML은 유지).

---

## 관측 (neo4j-off)

| run | cat-id | exit | pipeline_ok | elapsed | 비고 |
|-----|--------|------|-------------|---------|------|
| R0 | `cat-neo4j-off` | 0 | true | **291.6s** | S5 auto-start 대기 가능 (`20260622-2315`) |
| R1 | `cat-neo4j-off` | 0 | true | **96.2s** | `LINK_DISABLE_NEO4J_AUTO_START=1` (`20260623-0024`) |

| cat-id | exit | pipeline_ok | 비고 |
|--------|------|-------------|------|
| `cat-pdf-triple` | 0 | true | 3 source_file, ~496s |
| `cat-scanned-pdf` | 2 | — | `not_true_scan` fallback (`20260622-2309`), log·detail 필수 |

---

## μ-PROBE-SCAN-ω — born-digital 시도 (관측 전용)

**목적:** `cat-scanned-pdf` catalog와 **별개** — 잘못된 픽스처 클래스(born-digital Nature PDF) + Gemini 503 기록.  
**catalog:** `cat-scanned-pdf` **유지** (`not_true_scan` evidence 변경 없음).  
**R2:** **μ-PROBE-SCAN-R2** = 진짜 스캔 PDF `--path` 확보 시에만.

| 필드 | 관측 (`20260623-0116`) |
|------|------------------------|
| file | `s41467-021-23306-6.pdf` |
| pdf_class | **born-digital** (스캔 아님) |
| phase_r_ok | true |
| pipeline_ok | false |
| failed_step | `S4-4-NODE-dreamer-FLASH` |
| failure_class | **gemini_503** (스캔 품질 아님) |
| elapsed_sec | **3059.7** |
| exit | 2 |
| log | `logs/capability_probes/20260623-0116-cat-scanned-pdf-detail.json` |

**재시도 (선택):** quota/503 해소 후 동일 `--path` 명령 — live 재실행은 별도 μ.

---

## neo4j-off

- **방법:** `NEO4J_URI=bolt://127.0.0.1:19999` + `LINK_DISABLE_NEO4J_AUTO_START=1`
- **입력:** `tests/fixtures/s0b_draft_short.txt` 1건
- **합격:** Phase R ok + `pipeline_ok=true`
- **detail:** `neo4j_method`, `link_disable_neo4j_auto_start=true`

---

## pdf-triple

- **입력:** `s0a_paper.pdf` → `file-a/b/c.pdf` (동일 내용 3파일)
- **합격:** `distinct_source_file` 3 + pipeline ok

---

## scanned-pdf

- 우선순위: fixtures `*scan*.pdf` → `--path` → Desktop/KCH 탐색 → `not_true_scan` fallback exit 2

---

## 산출

| 경로 | 내용 |
|------|------|
| `logs/capability_runs/YYYYMMDD-HHMM-<cat-id>.json` | `log_capability_run.py` |
| `logs/capability_probes/YYYYMMDD-HHMM-<cat-id>-detail.json` | checklist·neo4j·files·pipeline_ok |

관련: [Q2-CAPABILITIES-spec.md](Q2-CAPABILITIES-spec.md), [BRANCH-2a-spec.md](BRANCH-2a-spec.md)
