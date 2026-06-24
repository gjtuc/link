# STAGE 0-SPINE — 읽기 철학·인터랙션 계약 (1차 초안)

> **진행 상태:** **μ-SPINE-02-API ✅** (e636830) → **μ-SPINE-03-UI** 착수 대기  
> **입력:** STAGE-0-1 (원인과 결과 지도), 사용자 철학 (메커니즘·저울질·유연 기준)  
> **다음:** `STAGE-0-SPINE-2-scenarios.md` ✅ → `STAGE-0-SPINE-3-acceptance.md` ✅ → `BRANCH-SPINE-spec.md` (μ-SPINE-00) ✅  
> **구현:** `BRANCH-SPINE-spec.md` (μ-SPINE-00, 설계만) — **본 문서 고정 후**

---

## 0-SPINE 한 줄 (0-1 보강)

**Link는 검증·재조립된 원인과 결과를 Spine(뼈대)으로 읽게 한다. 사용자는 화살표 hover로 인과를, 화살표 click·옆 패널로 메커니즘·검색을, Spine 목록으로 전체 흐름을 따른다. 원문 서사·목차 순서가 아니라 인과 메커니즘이 읽기의 기준이다.**

### 0-1과의 관계

| 0-1 | 0-SPINE |
|-----|---------|
| 원인과 결과 crumb + 지도 | **읽기 UX** — 지도만이 아님 |
| Strong/Gap/Weak | **Spine** = 읽기용 경로 (Strong chain 후보 확장) |
| NG-4 force graph only | **Spine 우선**, force graph는 배경 |
| δ 출처 숨기지 않음 | 링크·패널·검색에 **신뢰 층** 표시 |

---

## 북극성 (고정하지 않는 것)

| 고정하지 않음 | 대신 |
|---------------|------|
| fact / edge **개수** | **메커니즘이 읽히는가** |
| 뼈대 **1개** | 뼈대 **무제한**, 겹침 구분 |
| 단일 분해 해상도 | **거시(Spine)** / **미시(화살표)** 층 분리 |
| 절대 그래프 | 문서·맥락마다 **유연한** spine·저울 |

### 저울질 (트레이드오프)

- **뼈대 선명도** ↔ **링크(화살표) 선명도** — 한 화면·한 해상도로 동시 최대화 불가.  
- **조절** + **층 분리**(hover 짧게 / click·패널 깊게)로 둘 다 읽을 만한 구간을 찾는다.  
- 최적점은 **문서·맥락·사용자 깊이**마다 다름 — 미리 하나로 고정하지 않는다.

---

## 재쪼개기 (α ~ ζ) — SPINE 읽기

### α — 주체·목적

| ID | 내용 |
|----|------|
| α-1 | 사용자: **모르는 파일**을 인과 메커니즘으로 빠르게 이해 |
| α-2 | 배제: 저자 **주관 서사·목차 순서** 강요 |
| α-3 | 수단: AI가 쪼갠 crumb + 검증 인과 + (필요 시) 검색 |
| α-4 | 성공: Spine을 따라가며 **전체 메커니즘**이 보임 |

### β — 읽기 단위

| ID | 대상 | 동작 |
|----|------|------|
| β-1 | **화살표** | hover = 인과 (주 경로) |
| β-2 | **화살표** | click = 인과 상세·메커니즘·검색 |
| β-3 | **노드** | hover 없음; click 토글 → **팩트 상세** 패널 |
| β-4 | **Spine** | 목록·감싸기·따라가기 = **거시** |

### γ — 데이터 필드 (신규·확장)

| 필드 | 용도 |
|------|------|
| `link_sentence` (R4) | 화살표 hover 둘째 줄 |
| `link_mechanism` (R6) | 인과 상세 패널 본문 |
| `edge_kind` | CAUSES / BRIDGE — 문장·패널 톤 분기 |

### δ — 신뢰 층 (0-1 δ 계승)

| 층 | 표시 |
|----|------|
| CAUSES | `[검증 인과]` |
| BRIDGE | `[교차 연결]` · 인과 미검증 |
| R6 / 검색 | `분석 시 생성` / `검색 응답` · NG-3 웹 한 줄 |
| 가설 spine | `[가설 포함]` 필터 (기본 off) |

### ε — 범위

| ID | 1차 SPINE | 후속 |
|----|-----------|------|
| ε-1 | §1 전부 + §1f | — |
| ε-2 | §2~§9 철학·AC | 시나리오 문서 |
| ε-3 | §10-1 주제 묶음 | 다중 PDF 입체 읽기 |
| ε-4 | μ-CHUNK-STRUCT | 절·문단 청크 |

### ζ — 비유

| 비유 | 의미 |
|------|------|
| 점·선 지도 | force graph (배경) |
| **뼈대 줄기** | Spine — 메커니즘 따라가기 |
| **화살표 한 칸** | 인과 한 끼 |
| **옆 패널** | 현금(팩트)·인과 상세 서랍 |

---

## §1 — 인터랙션 계약 (확정)

### §1-1 노드

- hover 툴팁 **없음**.
- **짧은 click** → 옆 패널 `팩트 상세` **토글** (같은 노드 재click = 닫힘).
- 패널 열림 중에도 그래프·화살표 hover **차단하지 않음**.
- 발견성: 범례 또는 첫 분석 후 「노드를 누르면 상세」.
- 노드 상세는 **플로팅 툴팁이 아닌 옆 패널**; 1차에 기존 필드 재설계 없이 이전.

### §1d — 화살표 hover

| ID | 규칙 |
|----|------|
| §1d-1 | 지연 ~0.12s; 벗어나면 즉시 닫힘; 드래그·팬 중 off; 노드 패널과 독립 |
| §1d-2 | 1줄 태그 + 1줄 R4; `A → B` 기호 줄 없음; 방향은 문장 속 |
| §1d-3 | R4 = `link_sentence` 미리 생성; 없으면 A·B 필드 폴백; A·B subject 필수 |
| §1d-4 | T4 + B.state_change 반영; CAUSES/BRIDGE 틀 분리; 한 문장·말줄임 |
| §1d-5 | 2줄; R4 ~120자; 태그 짧은 고정 문구 |
| §1d-6 | hover에 **이유 없음** (깊은 층은 §1e) |
| §1d-7 | CAUSES `[검증 인과]`; BRIDGE `[교차 연결]` + 7b-아니오 (인과문 금지) |
| §1d-8 | R4 없을 때 기계 조합; 「자동」라벨 없음 (1차) |
| §1d-9 | R4 = 문서 언어; 태그 = 한국어 |
| §1d-10 | 화살표 간 즉시 교체; click 시 hover 닫음 |

**BRIDGE hover 예**

```
[교차 연결]
촉매는 서로 다른 문서에서 같은 주제로 연결된다(인과 미검증).
```

### §1e — 화살표 click · 패널

| ID | 규칙 |
|----|------|
| §1e-1 | 짧은 click 토글; 드래그·팬 무시; click 시 hover 닫음 |
| §1e-2 | 패널 **1개**; `팩트 상세` / `인과 상세` — 마지막 click이 내용 교체 |
| §1e-4 | R4 + R6(`link_mechanism`) + 양끝 요약 + 검색 입력 |
| §1e-5b | **B:** 기본 맥락 = A·B + R4·R6; 체크 `다른 업로드 문서도 참고` 시 배치 전체 추가 |
| §1e-5b-B5 | 화살표 바꿔도 체크 유지; 새 분석 시 체크 리셋 |
| §1e-6 | 출처·NG-3; BRIDGE 상세에 인과 미검증 고정 |
| §1e-8 | BRIDGE click = 비교·연결; CAUSES만 R6 인과 메커니즘 |

---

## §1f — Spine (확정)

### §1f-1 정의

- 병합 그래프 위 **연결 DAG** (**가지 허용**), **CAUSES edge ≥ 2**, **CAUSES ≥ 1** 필수.
- **CAUSES + BRIDGE** 포함 가능; BRIDGE만인 path는 spine 아님.
- BRIDGE 구간: §1d-7b·§1e-8; 목록 `(교차 k)`.
- **주 경로**: 루트→최장 리프; 라벨·따라가기 기본은 주 경로; 가지는 얇게 감싸기.
- 노드: 기본 검증·추출(1c-1); `[가설 포함]` 필터 기본 off.
- 개수 고정 없음; 긴 주 경로 우선·상한·더 보기.
- 라벨: `뼈대 N · {시작 subject} → {끝 subject}`.
- 후보: `find_strong_chains` 계열에서 시작 (알고리즘 동일화 가능).

### §1f-2 목록 UI

- 좌측: 위 뼈대 목록 / 아래 팩트·인과 패널.
- 분석 후 **최장 spine** 자동 선택.
- 필터: `[가설 포함]` off, `[교차 연결 포함]` on.
- spine 0: 「뼈대 없음 (인과 2칸 이상 필요)」+ Gap·밀도 힌트.
- 선택 spine 외 **dim**.

### §1f-3 ~ §1f-5

- 목록 hover = 미리보기; click = 선택 고정.
- 감싸기: DAG 전체; 주 경로 굵게; spine 색 + 비-spine dim.
- 공유 노드: 뱃지(소속 spine 수); 선택 spine 색 우선.
- 따라가기: `다음 칸`/`이전 칸` + 해당 화살표 §1d 툴팁; 주 경로 순.

### §1f-6

- **1차:** spine 목록만.
- **§10-1 (후속):** 주제 묶음 = spine 여러 개 묶음; 본 문서 범위 밖.

---

## §2 — 「메커니즘이 잘 보인다」(확정)

### §2-1 정의

메커니즘이 잘 보인다 = Spine(또는 동등 읽기 경로)을 따라 **시작→끝 흐름**을 읽을 수 있고, 각 CAUSES(·표시된 BRIDGE) 칸에서 **인과 문장·필요 시 심화**를 얻을 수 있다.

**아닌 것:** fact/edge 개수, Gap·Weak 제로, LLM·웹 100% 진실, abstract 한 줄 요약.

### §2-1c — 세 층

| 층 | 역할 |
|----|------|
| **Spine (거시)** | 줄기 선택·감싸기·따라가기 |
| **Link (미시)** | 화살표 hover R4 · click R6·검색 |
| **팩트** | 노드 click → 출처·δ |

**판정:** 세 층 모두 본 문서·시나리오에서 **언급**. **1차 AC(C-SPINE)** 는 **Spine + Link** 위주; 팩트 층은 C-SPINE-02·패널 필드로 부분 커버.

### §2-2 판정 주체 — 2a-혼합

- **시스템:** 관측 가능 신호 (spine 유무, R4 coverage, Gap·BRIDGE 라벨).
- **사용자:** 최종 「이해했다」— UAT·시나리오.
- **금지:** 제품이 「옳은 메커니즘」·「완전 이해」를 단정.

### §2-3 저울질 — §2-3c 휴리스틱

| ID | 조건 |
|----|------|
| §2-3c-1 | 선택 spine **주 경로** CAUSES edge ≥ 2 |
| §2-3c-2 | 그 spine 위 CAUSES edge **전부 R4** (또는 §1d-8 폴백) |
| §2-3c-3 | BRIDGE 칸: §1d-7b 문장 + `[교차 연결]` (인과 단정 없음) |
| §2-3c-4 | Gap가 spine 끝에 있으면 **라벨** (δ, 숨기지 않음) |

**PASS 후보:** §2-3c-1 **and** §2-3c-2. BRIDGE·Gap는 경고 가능, δ 위반 시 FAIL.

**조절:** 기본 **S(Spine) 우선** (최장 spine 자동); **L(Link)** = hover/click.

### §2-4 최소 PASS — P1 + P2 + P4

| ID | 신호 |
|----|------|
| **P1** | spine 목록 ≥ 1 |
| **P2** | 최장 spine 자동 선택·감싸기 |
| **P4** | CAUSES hover 2줄 (태그 + R4) |

(P3 따라가기·P5 R6·P6 출처·P7 겹침 색 — 2차 AC 또는 시나리오 UAT.)

### §2-5 · §2-6 요약

| 등급 | 예 |
|------|-----|
| **FAIL** | spine 0 (F1), spine UI 없음 (F4), BRIDGE 인과문 UI (F5) |
| **WARN** | R4 없음→폴백 (F2), Gap 끝 (W1), fact sparse (W2) |
| **spine 0** | 분석 실패 아님; 읽기 모드 비활성 + §1f-2e 메시지 |

### §2-7 시나리오 (→ STAGE-0-SPINE-2)

| ID | 요약 |
|----|------|
| S-SPINE-A | PDF 1, 인과 3칸 → P1+P2+P4 |
| S-SPINE-B | 인과 1칸 → spine 0, F1 |
| S-SPINE-C | PDF 2, BRIDGE → 7b + (교차 k) |
| S-SPINE-D | sparse 3 PDF → W2 |

---

## §3 — 주관 배제 vs LLM·검색 (확정, 추천)

### §3-1 정의

**주관 배제** = 저자 서사·목차 순서에 끌려가지 **않게 읽기 경로를 인과 지도로 고정**하는 것.  
**LLM·검색 사용 금지가 아님** — **출처·신뢰 층(δ)을 숨기지 않음**.

**배제:** 서사 프레이밍·원문 복붙·검증/가설/BRIDGE/검색 은폐·subject만으로 동일 사실·인과 단정.

**허용:** R4/R6 재구성, click·검색, Gap·Weak·가설 표시.

### §3-2 내용 층 (E/V/H/B/G/S)

| 층 | 의미 |
|----|------|
| **E** extracted | 파랑 — 원문 관측 |
| **V** verified CAUSES | 회색 + `[검증 인과]` |
| **H** hypothesis | 노랑·초록 — `[가설 포함]` 필터 |
| **B** BRIDGE | 보라 + `[교차 연결]` |
| **G** generated | R4·R6 — 분석 시 생성 |
| **S** searched | 패널 검색·질문 응답 |

**UI:** `인과 상세` 패널 **상단 한 줄** 층 태그 (예: `분석 시 생성 · 검증 인과 링크`).

### §3-3 R4·R6

- **MUST:** A·B 사이만; subject 포함; 원문 **장문 인용 금지**; deconstruct 톤.
- **MUST NOT:** 「저자는 주장」 서사; BRIDGE를 CAUSES처럼 R4/R6에서 단정; R6가 논문 결론 대체 톤.
- 폴백(§1d-8)도 **G층** 동일.

### §3-4 검색 (§1e-5b-B)

- 기본 **좁음**; 체크 시 **넓음** + 패널 `교차 비교 모드` 한 줄.
- 넓음: **나열·대조**만 — 문서 간 인과 **합침 단정** 금지.
- 웹: **NG-3** 고정 문구; S층 답은 R6 **아래 대화 블록** (덮어쓰기 없음).

### §3-5 구조 청크

- 절·문단 청크 = ingest **분할 힌트** (μ-CHUNK-STRUCT).
- **읽기 순서** = Spine·화살표만; 저자 목차 ≠ 읽기 순서.

### §3-6 · §3-7

- 라벨 **필수** (인과 패널, 검색, BRIDGE, Gap, 넓은 맥락).
- **FAIL:** BRIDGE를 검증 인과로 표시; 검색 답 층 구분 없음.
- **WARN:** R4 폴백만; 넓은 맥락 + BRIDGE spine.

---

## §4 — Spine 성분·AC 정리 (확정, 추천)

§1f 정의와 C-SPINE·기존 코드 **단일 표**. 중복 정의 금지.

### §4-1 용어 일치

| 제품 | 코드·기존 | 비고 |
|------|-----------|------|
| **Spine** | `find_strong_chains` 후보 + BRIDGE·가지·주경로 확장 | UI·`spine_index` (μ-SPINE) |
| **Strong chain** | `skeleton.strong_chain_count` | Spine **후보군**; 동의어 아님 — Strong ⊂ Spine 후보 |
| **Gap / Weak** | `skeleton/rules.py` | Spine **끝·주변** 경고; spine 성분 아님 |
| **BRIDGE** | `corpus_bridge` | Spine **포함 가능** (§1f-1b); CAUSES≥1 필수 |
| **Outline** | `#skeleton-outline` | 참고 목록; Spine **대체 아님** (§7) |

### §4-2 Spine 성분 체크리스트 (구현 μ)

| 성분 | MUST | AC |
|------|------|-----|
| `spine_id`, `node_ids`, `edge_ids` | ✅ | fixture schema |
| `main_path` (주 경로) | ✅ 가지 spine | C-SPINE-07 |
| `bridge_count` | ✅ | C-SPINE-06 |
| `label` = `뼈대 N · A → B (교차 k)` | ✅ | copy |
| `link_sentence` per CAUSES edge | ✅ | C-SPINE-10 |
| R6 per CAUSES edge (click) | SHOULD 1차 | C-SPINE-03 |

### §4-3 §8 흡수

검색·신뢰·NG-3 → **§3·§1e**로 통합. 별도 §8 문서 **불필요**.

### §4-4 1차 AC 범위 (§2와 합치)

| 범위 | C-SPINE |
|------|---------|
| **1차 PASS** | 05, 01, 09 (P2+P4+P1) |
| **1차 SHOULD** | 02, 03, 06, 10, 12 |
| **2차** | 04, 07, 11, 13~15, 08 |

---

## §5 — Spine 선택·저울 조절 (확정, 추천)

### §5-1 조절 주체 — 혼합 (§2-2와 동일)

| 누가 | 무엇 |
|------|------|
| **시스템 (기본)** | 최장 spine 자동 선택; S(Spine) 우선; R4 생성; 필터 기본값 |
| **사용자** | spine 목록 click; `[가설 포함]`·`[교차 연결 포함]`; 5b-B 넓은 맥락; 검색·질문 |
| **1차 없음** | 분해 굵기 슬라이더; spine 개수 상한 사용자 설정 |

**L(링크) 깊이:** hover/click — **사용자가 칸마다** 선택. 시스템이 한 해상도로 고정하지 않음.

### §5-2 Spine 선택 규칙

| ID | 규칙 |
|----|------|
| §5-2a | 분석 직후 **주 경로 최장** spine 자동 선택 (§1f-2b) |
| §5-2b | 사용자 목록 click → **선택 고정**; hover = 미리보기 |
| §5-2c | 동일 길이 tie → **CAUSES 비율 높은** 쪽 우선 |
| §5-2d | spine **개수 제한 없음**; UI 상한 + 더 보기 |

### §5-3 저울 (S ↔ L)

| ID | 규칙 |
|----|------|
| §5-3a | 기본 뷰 = **S** (spine 감싸기·dim) |
| §5-3b | **L** = 화살표 hover R4 → click R6·검색 |
| §5-3c | 시스템이 spine **노드 수를 동적 조절하지 않음** (1차); 촘캠함은 **사용자 click** |
| §5-3d | §10-1 주제 묶음 = **S 메타** (여러 spine); 후속 μ |

### §5-4 필터 기본값 (§1f-2d 재확인)

| 필터 | 기본 |
|------|------|
| `[가설 포함]` | **off** |
| `[교차 연결 포함]` | **on** |

---

## §6 — 절·문단 청크 (확정, 추천) → μ-CHUNK-STRUCT

**목적:** 인과가 **문단·절 단위**로 끊기지 않게 ingest 분할. **읽기 순서는 Spine**(§3-5).

### §6-1 분할 우선순위

| 순위 | 규칙 |
|------|------|
| 1 | 텍스트 **절 제목** 감지 (`1. Introduction`, `##`, 전부 대문자 한 줄 등) |
| 2 | 절 내부 **문단**(빈 줄) 경계 |
| 3 | 절이 ~8 000자 초과 → 절 **안에서만** 문단 단위 분할 |
| 4 | 제목 없음 → 현행 `chunk_text` (문단+8k) **폴백** |
| PDF | 페이지 묶음보다 **본문 합친 뒤 절/문단** 우선 |

### §6-2 청크 라벨

- `paper.pdf · § Methods` / `§ Results (2/3)` — **p.3-5** 대신 **논리 단위**.
- 북마크 목차는 **보조**; 본문 제목 감지 **주**.

### §6-3 MUST NOT

- 청크 = 저자 **목차 순 읽기** ❌  
- 청크 경계 = **인과 검증 범위 상한** (청크 넘 CAUSES는 1차 여전히 드묾 → §10·bridge 확장은 별도)

### §6-4 AC (μ-CHUNK)

| ID | 조건 |
|----|------|
| C-CHUNK-01 | PDF fixture: 라벨에 `§` 또는 절명 |
| C-CHUNK-02 | 문단 중간 **하드 split** 없음 (fixture) |

---

## §7 — 기존 UI와 관계 (확정, 추천)

| UI | 역할 | SPINE 1차 |
|----|------|-----------|
| **Spine 목록** | 1급 읽기 진입 | ✅ 전면 |
| **force graph** | 탐색·배경 | dim, 클릭·hover는 §1 |
| **skeleton-health** (Gap/Strong/Weak) | **품질 요약** | 유지; Strong 수 ≠ spine 수 |
| **skeleton-outline** | claim 트리 **참고** | 접기 가능; spine **대체 아님** |
| **recompose** (Report/Narrative/Rewrite) | ε 텍스트 **후속** | 탭 유지; spine과 **연동 optional** 2차 |
| **corpus-hint** | 런 간 기록 | spine과 **독립** |

**§7 계약:** SPINE 출시 후에도 skeleton·recompose **삭제 안 함** — 역할 분리.

---

## §9 — sparse·빈 경우 (확정, 추천)

### §9-1 신호

| 상황 | 등급 | UI |
|------|------|-----|
| spine 0 | §2 F1 | §1f-2e 메시지 |
| fact/청크 < 3 (휴리스틱) | W2 | 「팩트가 적음 — 밀도·PDF 추출 확인」 |
| edge 0, fact > 0 | WARN | 점만 많음; 인과 부족 |
| Gemini 503 등 | FAIL 분석 | 기존 단계 로그; spine 무관 |

### §9-2 제품 약속 (1차)

- sparse여도 **실패가 아님** — §2: 읽기 모드 제한.
- 제안: **점 지도** + Gap + (후속) 밀도 μ — **빈 화면 금지**.

### §9-3 AC

| ID | 조건 |
|----|------|
| C-SPINE-16 | sparse fixture: W2 copy 존재 |
| C-SPINE-17 | spine 0 + fact≥1: 그래프에 노드 표시 |

---

## §10 — 다중 PDF · §10-1 주제 묶음 (확정, 추천)

### §10-1 정의

**TopicBundle(주제 묶음)** = **여러 Spine** + **공유 노드**를 하나의 **읽기 묶음**으로 표시.  
**인과를 한 줄로 합치지 않음** — §3-4·§1f-1b와 동일.

### §10-2 묶음 생성 (휴리스틱, 1차)

| 신호 | 가중 |
|------|------|
| 동일 `subject` 노드 **공유** | ✅ |
| BRIDGE edge 연결 | ✅ |
| (후속) subject **정규화/유사** | 2차 μ |
| state_change 동일 | **필수 아님** |

**1차:** 공유 노드 ≥1 인 spine 둘 이상 → 후보 묶음.

### §10-3 UI (2차 μ `μ-SPINE-BUNDLE`)

- 묶음 라벨: `[주제: 촉매]` + 소속 spine 목록.
- 묶음 hover → 소속 spine **동시 약한 하이라이트**.
- 묶음 click → spine 목록 **필터**.
- **1차 SPINE:** spine 목록만; 묶음 UI **후속**.

### §10-4 관계

| 기능 | 역할 |
|------|------|
| BRIDGE | 팩트 **한 점선** |
| Spine | **인과 경로** |
| 주제 묶음 | spine **여러 개** 비교·모음 |
| 5b-B 넓음 | 질문 시 **문서 풀** |

### §10-5 MUST NOT

- 묶음 = 하나의 메커니즘 단정 ❌ · 묶음명 = 저자 결론 ❌

### §10-6 AC (2차)

| ID | 조건 |
|----|------|
| C-BUNDLE-01 | 2 PDF: 묶음 ≥1 또는 「묶음 없음」 |
| C-BUNDLE-02 | 묶음 hover → spine id 집합 하이라이트 |

---

## NON-GOALS (NG-SPINE-*)

| ID | 내용 |
|----|------|
| NG-SPINE-1 | fact/edge 개수 = 성공 |
| NG-SPINE-2 | 저자 목차 순서 = 읽기 순서 |
| NG-SPINE-3 | BRIDGE를 검증 인과와 동일 UI·문장 |
| NG-SPINE-4 | 노드 hover로 인과 읽기 |
| NG-SPINE-5 | 검색 맥락 기본 = 업로드 전체 (기본은 5b-좁음) |
| NG-SPINE-6 | μ-SPINE 전 설계 없이 UI 구현 |

---

## 완료 조건 초안 (C-SPINE-*) — §0-SPINE-3에서 확정

| ID | 조건 | 검증 방향 |
|----|------|-----------|
| C-SPINE-01 | 화살표 hover 2줄 (태그+R4) | fixture + UI test |
| C-SPINE-02 | 노드 click 패널 토글 | UI test |
| C-SPINE-03 | 화살표 click `인과 상세` + R6 | fixture JSON |
| C-SPINE-04 | 5b-B 체크 시 넓은 맥락 | API mock test |
| C-SPINE-05 | spine 목록 + 최장 자동 선택 | E2E fixture |
| C-SPINE-06 | BRIDGE spine `(교차 k)` + 7b 문장 | fixture |
| C-SPINE-07 | 가지 spine 주 경로 굵게 | snapshot |
| C-SPINE-08 | spine 0 메시지 | copy test |
| C-SPINE-09 | §2 P1: spine≥1 또는 F1 메시지 | E2E |
| C-SPINE-10 | §2-3c-2: CAUSES R4 또는 폴백 | fixture |
| C-SPINE-11 | §2-3c-3: BRIDGE 태그·7b 문장 | fixture |

**1차 PASS 묶음:** C-SPINE-05 + C-SPINE-01 + C-SPINE-09 (= P2 + P4 + P1).

| C-SPINE-12 | §3-2: 패널 층 태그 | UI test |
| C-SPINE-13 | §3-3: R4/R6 장문 원문 인용 없음 | heuristic test |
| C-SPINE-14 | §3-4: 5b-B 넓음 시 교차 비교 라벨 | UI test |
| C-SPINE-15 | §3-4: NG-3 문구 (검색 시) | copy test |
| C-SPINE-16 | §9: sparse W2 copy | copy test |
| C-SPINE-17 | §9: spine 0 + nodes visible | E2E |

---

## 대기 큐 (§2 ~ §10)

| § | 주제 | 상태 |
|---|------|------|
| §2 | 「메커니즘이 잘 보인다」— 운영 정의 | ✅ 본 문서 |
| §3 | 주관 배제 vs LLM·검색 | ✅ 본 문서 |
| §4 | Spine 성분·AC 정리 | ✅ 본 문서 |
| §5 | spine 선택·저울 조절 | ✅ 본 문서 |
| §6 | 절·문단 청크 | ✅ 본 문서 → μ-CHUNK-STRUCT |
| §7 | skeleton / recompose / graph | ✅ 본 문서 |
| §8 | 검색 신뢰 | ✅ §3·§1e 흡수 |
| §9 | sparse·빈 경우 | ✅ 본 문서 |
| §10 | 다중 PDF · §10-1 주제 묶음 | ✅ 본 문서 (묶음 UI = 2차 μ) |

---

## 구현 순서 (PROCESS.md)

```
0-SPINE-1  ✅ STAGE-0-SPINE-philosophy.md
0-SPINE-2  ✅ STAGE-0-SPINE-2-scenarios.md (완료본)
0-SPINE-3  ✅ STAGE-0-SPINE-3-acceptance.md (완료본)
μ-SPINE-00 ✅ BRANCH-SPINE-spec.md + spine_design_sample pytest
μ-SPINE-UNLOCK ✅ branch_spine_unlocked
μ-SPINE-01 ✅ contract.py + rationale.py (1c11cc5)
μ-SPINE-02 ✅ index.py + main_path.py (ba2bb4d)
μ-SPINE-02-API ✅ api_payload + pipeline_batch (e636830)
μ-SPINE-03-UI … index.html
```

**병행 (별 μ):** μ-CHUNK-STRUCT (절·문단 청크), μ-2b 유지보수.

---

## 코드·문서 링크

| 항목 | 경로 |
|------|------|
| 0-1 계약 | `STAGE-0-1-product-definition.md` |
| μ-SPINE-00 | `BRANCH-SPINE-spec.md` · [읽기 가이드](BRANCH-SPINE-spec-읽기가이드.md) |
| 시나리오 | `STAGE-0-SPINE-2-scenarios.md` |
| AC | `STAGE-0-SPINE-3-acceptance.md` |
| Strong chain | `deconstructor/skeleton/rules.py` `find_strong_chains` |
| BRIDGE | `deconstructor/web/corpus_bridge.py` |
| Edge tooltip (현状) | `deconstructor/viz/visualizer.py` `_edge_tooltip` |
| 진행 규칙 | `PROCESS.md` |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-22 | 1차 초안 — 대화 §1·§1f 확정 반영 |
| 2026-06-22 | §2 확정 — 2a-혼합, §2-3c, P1+P2+P4, 1차 AC Spine+Link |
| 2026-06-22 | §3 확정 (추천) — E/V/H/B/G/S 층, 5b-B 교차 비교 라벨, NG-3 |
| 2026-06-22 | §4·§5 확정 (추천) — AC 정리, 시스템 기본+사용자 선택, S/L 저울 |
| 2026-06-22 | §6·§7·§9 확정 (추천) — μ-CHUNK, UI 역할 분리, sparse |
| 2026-06-22 | §10 확정 (추천) — TopicBundle 2차 μ, BRIDGE·5b-B와 역할 분리 |
