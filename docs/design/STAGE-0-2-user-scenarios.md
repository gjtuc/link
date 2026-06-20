# STAGE 0-2 — 사용자 시나리오 (완료본)

> **진행 상태:** 1차 작성 → 재쪼개기 → 점검·수정 → **주석 고정 완료**  
> **입력:** [STAGE-0-1-product-definition.md](STAGE-0-1-product-definition.md) (α~ζ, C-*, NG-*)  
> **다음:** `STAGE-0-3-acceptance-criteria.md` (본 문서 S0-*, F0-*, A0-* 를 입력으로 사용) — **0-3 완료**  
> **다음 단계:** [STAGE-0-5-implementation-roadmap.md](STAGE-0-5-implementation-roadmap.md) — Sprint 0

---

## 0-2 목적

0-1 계약 문장이 **누가·무엇을·어떤 순서로** Link UI/CLI를 쓰면 성립하는지 **재현 가능한 시나리오**로 고정한다.  
각 시나리오는 0-1의 γ(因·과), ζ(요리 비유), C-*, NG-* 에 **매핑**된다.

---

## 시나리오 목록 (1차)

| ID | 이름 | 0-1 근거 | 우선순위 |
|----|------|----------|----------|
| **S0-A** | 논문 PDF 1편 — 뼈대·因→과 지도 | α-2, α-4, ζ-1~4, β-1 | P0 |
| **S0-B** | 보고서 초안(텍스트) — 비약·약한 因 | α-4, γ Gap/Weak, ζ-3 | P0 |
| **S0-C** | 자료 여러 편 — 뜻밖의 因→과 | α-4, **2단계** | P1 |
| **S0-D** | 뉴스 URL — 짧은 완성품 | α-2 부록, ingest `summarize` | P2 |
| **S0-E** | 분석 중·후 Human-in-the-loop | γ 가설, ζ-5 | P1 |
| **S0-F** | 디버그·재현 (개발자/본인) | δ 숨기지 않음 | P2 |

---

## S0-A — 논문 PDF 1편 (P0)

### A-1. 사용자 스토리

> 연구자가 **논문 PDF 1개**를 Link UI에 올리고 「전체 분석 시작」을 누른다.  
> **완성품(ζ-1)** 이 **청크 단위(β-1)** 로 해체되고, 因·과 그래프와 (향후) 뼈대 강약을 본다.  
> **재조리 텍스트(ε-2~4)는 기대하지 않는다** (C-5).

### A-2. 단계 (Given / When / Then)

| Step | Given | When | Then (MUST) |
|------|-------|------|-------------|
| A-2-1 | PDF 업로드 | 분석 시작 | ingest: **요약 없음**, `total_chars ≈ 원문` (C-1) |
| A-2-2 | ingest 완료 | Deconstruct×청크 | completed_facts **청크당 다수** (β-2 목표, 3단계) |
| A-2-3 | 파이프라인 완료 | 그래프 표시 | 파랑(extracted)+노랑/초록(promoted)+✕(dropped) (γ) |
| A-2-4 | stub FC | UI 상태 | 「미검증 가설」또는 `fact_checker: stub` (C-4) |
| A-2-5 | 분석 완료 | 사용자 판독 | **NG-2 위반 아님**: 노드 적어도 실패 아님, **Gap/Strong**이 중요 (C-3) |

### A-3. 0-1 매핑

| 0-1 | S0-A에서의 의미 |
|-----|----------------|
| β-3 | 라벨 `file.pdf (p.3-4) · 2/12` — **C-2 TODO** (메타 필드) |
| NG-1 | PDF 403자 요약만 → **시나리오 실패** |
| NG-4 | force graph만 → **부분 성공**, Outline(9단계) 없으면 불완전 |

### A-4. 실패 시나리오 (F0-A*)

| ID | 조건 | 기대 UX |
|----|------|---------|
| F0-A1 | PDF 텍스트 0자 | 명확한 오류, 단계 `S2-DOC-*` |
| F0-A2 | ingest summarize 모드 | **F0-A2 = NG-1 위반**, 문서화된 안티패턴 |
| F0-A3 | 청크 12× LLM 타임아웃 | 진행률·중단·재시도 (UI) |

### A-5. 현재 구현 (2026-06)

| Step | 상태 |
|------|------|
| A-2-1 | ✅ document ingest + 청크 |
| A-2-2 | ⚠️ 청크당 fact 수 적음 (3단계·non-atomic 미완) |
| A-2-3 | ✅ pyvis + provenance |
| A-2-4 | ✅ `/api/status` stub |
| A-2-5 | ❌ Skeleton Health 패널 없음 (9단계) |

---

## S0-B — 보고서 초안 텍스트 (P0)

### B-1. 사용자 스토리

> 사용자가 **직접 쓴/붙여넣은 보고서 초안**을 텍스트 상자에 넣는다.  
> 「결론은 그럴듯한데 근거·인과가 약한 문장」을 **Gap·Weak** 으로 드러내고 싶다 (γ).

### B-2. 단계

| Step | When | Then |
|------|------|------|
| B-2-1 | 짧은 텍스트 (<2k) | 1청크, 요약 **없음** |
| B-2-2 | 긴 텍스트 (>2k) | `텍스트 #1 · 청크 k/n` (document ingest와 동일 정책) |
| B-2-3 | Skeptic 완료 | 약한 因→과는 기각 또는 weak (ζ-3) |
| B-2-4 | 사용자 | **비약 구간**을 그래프/향후 Outline에서 식별 |

### B-3. 0-1 매핑

- α-3: 붙여넣은 글 = 완성품, **별도 요약 금지**
- δ: 약함을 **숨기지 않음** — promoted stub를 「검증됨」처럼 보이면 **실패** (C-4)

### B-4. 실패 (F0-B*)

| ID | 조건 |
|----|------|
| F0-B1 | 2k+ 텍스트가 2–5문장으로 줄어듦 (NG-1) |
| F0-B2 | conclusion fact만 있고 전부 Gap — **정상 결과** (뼈대 약함 드러남) |

### B-5. 현재 구현

| Step | 상태 |
|------|------|
| B-2-1~2 | ✅ extract_batch 긴 텍스트 청크 |
| B-2-3 | ✅ Skeptic |
| B-2-4 | ❌ Outline/Gap UI |

---

## S0-C — 자료 여러 편 · 교차 因→과 (P1)

### C-1. 사용자 스토리

> 논문 PDF + 보조 PDF(또는 메모 txt)를 **동시에** 넣는다.  
> **서로 다른 완성품** 사이에서 **뜻밖의 因→과**(브릿지)를 보고 싶다 (α-4, 2단계).

### C-2. 단계

| Step | Then (목표) | 현재 |
|------|-------------|------|
| C-2-1 | 소스별 ingest·청크 | ✅ |
| C-2-2 | **Corpus fact pool** merge | ✅ batch + bridge |
| C-2-3 | Cross-doc bridge (subject match) | ✅ MVP (non-LLM) |
| C-2-4 | UI 「교차 연결 N건」 | ✅ Sprint 2 |
| C-2-5 | 출처별 필터 (파일 A/B) | ❌ C-2 메타 |

### C-3. 0-1 매핑

- **0-2에서 S0-C는 「목표 시나리오」** — 0-1 α-4의 다중 입력 확장  
- NG-2: 두 파일 합쳐 노드만 많아짐 ≠ 성공 — **브릿지 edge** 또는 explicit 「교차 0건」

### C-4. 실패 (F0-C*)

| ID | 조건 |
|----|------|
| F0-C1 | 같은 subject 다른 UUID만 2개 — **중복**, 교차 아님 |
| F0-C2 | merge_graph + **bridge 계산** — bridge 0건이면 UI 「교차 0건」 (Sprint 2 ✅) |

### C-5. 0-2에서의 상태

**Sprint 2 MVP ✅** — subject-match bridge + 「교차 N/0건」 UI. Skeptic cross-doc·출처 필터(C-2-5)는 Later.

---

## S0-D — 뉴스 URL (P2)

### D-1. 사용자 스토리

> 짧은 **뉴스 기사 URL** 하나를 넣는다. 완성품이 짧으므로 **summarize ingest** 허용 (α-2 부록, `LINK_DOCUMENT_INGEST=summarize` 또는 HTML 경로).

### D-2. 단계

| Step | Then |
|------|------|
| D-2-1 | HTML → 2–5문장 factual (기존 `_URL_PROMPT`) |
| D-2-2 | 동일 코어 DAG (ζ-2~5) |
| D-2-3 | Tavily live 시 web FC (NG-3: **논문 진실 아님**, UI 표시) |

### D-3. 0-1 매핑

- S0-D는 **S0-A와 ingest만 다름** — **혼동 금지**: 논문 PDF에 summarize 쓰면 F0-A2
- C-4, NG-3: 뉴스 + Tavily = **web 검증**, 논문 ≠

### D-4. 현재 구현

| Step | 상태 |
|------|------|
| D-2-1 | ✅ |
| D-2-2 | ✅ |
| D-2-3 | stub 기본 (TAVILY_DISABLED) |

---

## S0-E — Human-in-the-loop (P1)

### E-1. 사용자 스토리

> 그래프에서 **파란 노드(extracted)** 우클릭 → 가설 추가 → 노란 노드 (ζ-5).  
> 사용자 因→과 가설이 **Fact-Checker·Skeptic** 을 거친다.

### E-2. 단계

| Step | Then |
|------|------|
| E-2-1 | POST `/api/human-hypothesis` |
| E-2-2 | `author=human`, inferred/pending → promoted/dropped |
| E-2-3 | δ: stub promote 시 **미검증** 표시 유지 |

### E-3. 현재

✅ MVP (Neo4j optional). E-2-3 C-4와 동일 이슈.

---

## S0-F — 디버그·재현 (P2)

### F-1. 사용자 스토리

> `/debug.html`, `/api/debug/pipeline` 로 **왜 노드/선이 이 수인지** 확인 (δ).

### F-2. Then

- `completed_facts`, orphan_extracted, fact_checker_mode 표시  
- 0-2 **F0-*** 재현 시 로그·`failed_step` 추적

---

# 0-2 자기 점검 — 재쪼개기 (σ)

### σ-1. 시나리오 커버리지 vs 0-1

| 0-1 | σ-1 판정 | 조치 |
|-----|----------|------|
| α-4 출력 | S0-A,B,E ✅ / S0-C 목표만 | C를 P1 gap 명시 ✅ |
| β 전체 | S0-A,B ingest ✅ / β-2,β-3 코드 gap | A-5, C-2-5 기록 ✅ |
| γ | 전 시나리오 그래프색 ✅ / Gap UI ❌ | 0-3 A-* 로 |
| ζ | S0-A~E 모두 파이프라인 단계 매핑 ✅ | — |
| C-1~5 | 시나리오별 표에 분산 ✅ | 0-3에서 통합 |
| NG-1~4 | F0-A2,B1,C2,D3 등 ✅ | — |

### σ-2. 빠진 시나리오 추가

| ID | 이유 |
|----|------|
| **S0-E** | 0-1 Dreamer 외 **human** 가설 — 코드에 있음 |
| **S0-F** | δ 재현 — debug.html |

### σ-3. 우선순위 수정

- P0: S0-A, S0-B (논문·보고서 = 당신 Pain)  
- P1: S0-C, S0-E  
- P2: S0-D, S0-F  

### σ-4. 모순 제거

- **모순:** 「모든 입력 요약 금지」 vs 뉴스 URL  
- **해결:** ingest **모드 분기** — document vs summarize (S0-A/B vs S0-D), 문서에 명시 ✅

### σ-5. UI 진입점 ↔ 시나리오

| UI | 시나리오 |
|----|----------|
| 파일 탭 PDF | S0-A, S0-C |
| 텍스트 탭 | S0-B |
| URL (텍스트/링크) | S0-D |
| 그래프 우클릭 | S0-E |
| debug.html | S0-F |

---

# 0-2 Acceptance 요약 (A0-*)

| ID | 시나리오 | 핵심 Then |
|----|----------|-----------|
| A0-A | S0-A | 원문 char 유지 + 청크 + provenance 그래프 |
| A0-B | S0-B | 긴 붙여넣기 청크, 약한 뼈대 **드러남** |
| A0-C | S0-C | (목표) 교차 edge 또는 「0건」명시 |
| A0-D | S0-D | HTML summarize OK, 코어 동일 |
| A0-E | S0-E | human 가설 → 색·검증 경로 |
| A0-F | S0-F | debug로 ingest·FC mode·fact 수 |

---

# 0-3 진입 시 참조

- A0-* → 0-3 **측정 가능** Acceptance 로 변환  
- F0-* → 0-3 **회귀·안티패턴** 테스트  
- A-5, B-5, C-5 **현재 gap** → 0-4 현재 vs 목표  

---

## 코드베이스 링크 (0-2 주석 고정)

| 파일 | STAGE 0-2 |
|------|-----------|
| `deconstructor/web/server.py` | UI 시나리오 S0-A~F ↔ API |
| `web/index.html` | 입력 탭 = 시나리오 진입 |
| `docs/design/STAGE-0-1-product-definition.md` | 0-2 입력 |
