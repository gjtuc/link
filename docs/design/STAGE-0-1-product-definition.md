# STAGE 0-1 — 제품 한 줄 정의 (완료본)

> **진행 상태:** 1차 작성 → 재쪼개기 → 점검·수정 → **주석 고정 완료**  
> **다음:** `STAGE-0-2-user-scenarios.md` (본 문서의 α~ζ, C-*, NG-* 를 입력으로 사용) — **0-2 완료**  
> **다음 단계:** `STAGE-0-3-acceptance-criteria.md`

---

## 0-1 수정본 (계약 문장)

**Link는 겉으로 완성된 서술(논문·보고서 등)을 원인과 결과 crumb으로 해체하고, Skeptic·Fact-Checker·출처(provenance)로 논리 뼈대의 튼 곳·빈 원인·약한·거짛 원인→결과를 숨기지 않고 보여 준다. 이 지도를 바탕으로 이후 단계에서 글을 재조립할 수 있다.**

### 문장별 주석

| 구절 | 의미 | 검증 방법 |
|------|------|-----------|
| 겉으로 완성된 서술 | PDF/DOCX/긴 텍스트 등 **출판·제출 수준** 글 | ingest 후 char 수 ≈ 원문 |
| 원인과 결과 crumb | `AtomicFact.subject` + `state_change` | Deconstruct FactList |
| 해체 | **분해** (요약 아님) | `LINK_DOCUMENT_INGEST=document` |
| Skeptic·Fact-Checker | 규칙·검증 레이어 | `verified_edges`, dropped |
| 튼/빈/약/거짛 | Strong/Gap/Weak/False (9단계 UI) | skeleton index |
| 숨기지 않고 | stub·drop·reject **라벨링** | UI `fact_checker: stub` 등 |
| 재조립 **할 수 있다** | 능력·방향 (0-1 범위) | 10단계에서 산출물 정의 |

---

## 재쪼개기 (α ~ ζ)

### α — 주체·입출력

| ID | 내용 |
|----|------|
| α-1 | 사용자: 연구자·분석가·보고서 작성자 |
| α-2 | 입력: 완성품 서술 (PDF/DOCX/긴 txt). URL/HTML은 **1단계 ingest 부록** |
| α-3 | 금지: 요약본만 Deconstruct, LLM 내러티브 대체 |
| α-4 | 출력(0-1): 원인과 결과 지도 + **뼈대 강약**. 재조리 **텍스트**는 10단계 |

### β — 해체(부스러기)

| ID | MUST | MUST NOT |
|----|------|----------|
| β-1 | subject + state_change 분해 | 2–5문장 요약 → Deconstruct |
| β-2 | non-atomic → Verify 재분해 | 1회 LLM 후 전부 atomic |
| β-3 | 출처(파일·페이지·청크) | 출처 없는 fact |

### γ — 원인과 결과 (제품 정의)

| 기호 | 데이터 | UI |
|------|--------|-----|
| 원인 | subject | 노드 라벨 |
| 결과 | state_change | 툴팁 |
| 원인→결과 검증 | `verified_edges` | 회색 실선 |
| 원인→결과 가설 | inferred/promoted/dropped | 노랑/✕ |
| 빈 원인 | in-edge 없는 conclusion | Gap (9단계) |
| 약한 원인→결과 | INCONCLUSIVE 등 | 점선/Weak |

### δ — “왜곡 없이”의 정확한 의미

- **NOT:** LLM·규칙이 100% 진실 보장  
- **IS:** 검증/가설/기각/ stub **출처를 숨기지 않음**  
- Ingest 단계 LLM **요약** = 왜곡 유입 → document 모드에서 **금지**

### ε — 재조립 범위

| ID | 산출 | 단계 |
|----|------|------|
| ε-1 | 뼈대 지도(읽기) | 0~9 |
| ε-2~4 | report / verified narrative / rewrite | **10단계** |

### ζ — 요리 비유 (고정)

| 비유 | ζ-ID | 파이프라인 |
|------|------|------------|
| 완성품 | ζ-1 | Ingest |
| 부스러기 | ζ-2 | Deconstruct + Verify |
| 상함·태움·소스 잘못 | ζ-3 | Fact-Checker drop, Skeptic reject |
| 괜찮은 부위 | ζ-4 | extracted + verified |
| 빈 연결 시식 | ζ-5 | Dreamer |
| 재조리 | ζ-6 | 10단계 |

---

## 완료 조건 (C-*)

| ID | 조건 | 구현 단계 |
|----|------|-----------|
| C-1 | document ingest 시 요약 없이 원문 char 수 UI | 1 ✅ partial, 9 UI |
| C-2 | fact마다 출처(파일·청크·페이지) | 1 TODO 메타 |
| C-3 | Strong/Gap/Weak/False/Hypothesis 정의 | 7, 9 |
| C-4 | stub Fact-Checker → 「미검증 가설」 표시 | 6, UI ✅ partial |
| C-5 | 재조리 텍스트 출력 | **10단계 (0-1 범위 밖)** |

---

## NON-GOALS (NG-*)

| ID | 내용 |
|----|------|
| NG-1 | 자동 요약 = 분해 |
| NG-2 | 노드 많음 = 성공 |
| NG-3 | Tavily/web = 논문 진실 |
| NG-4 | force graph only = 「한눈에 뼈대」 |

---

## 코드베이스 링크 (0-1 주석 고정 위치)

| 파일 | STAGE 0-1 블록 |
|------|----------------|
| `deconstructor/web/extract.py` | Ingest: 압축≠분해 |
| `deconstructor/web/pipeline_batch.py` | 배치 = 완성품→파이프라인×N |
| `deconstructor/graph/builder.py` | 코어 DAG (0-1 변경 대상 아님) |
| `README.md` | 제품 서약 요약 → 본 문서 링크 |

---

## 0-2 진입 시 반드시 참조할 것

- α-4, β-3 → 시나리오마다 입·출력 명시  
- γ → S0-* 각각 Strong/Gap 기대  
- NG-1~4 → 시나리오 **실패 케이스** 작성  
- C-1~5 → 시나리오 **Acceptance** 매핑  
