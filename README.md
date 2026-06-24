# Deconstructor (Link) — 원인과 결과 논리 뼈대 엔진

**완성품(논문·보고서·서술) → 원인과 결과 crumb 해체 → Skeptic·Fact-Checker로 뼈대 강약 드러내기 → (재조립)**

겉으로 잘 조리된 글을 **부위별로 해체**하고, 튼 연결·빈 원인·약한·거짛 원인→결과를 **숨기지 않고** 보여 준다.  
코어: Deconstruct → Verify → Dreamer → Fact-Checker → Skeptic → Weaver.

> **0-1 계약:** [docs/design/STAGE-0-1-product-definition.md](docs/design/STAGE-0-1-product-definition.md)  
> **0-2 시나리오:** [docs/design/STAGE-0-2-user-scenarios.md](docs/design/STAGE-0-2-user-scenarios.md)  
> **0-3 Acceptance:** [docs/design/STAGE-0-3-acceptance-criteria.md](docs/design/STAGE-0-3-acceptance-criteria.md)  
> **0-4 Gap:** [docs/design/STAGE-0-4-current-vs-target.md](docs/design/STAGE-0-4-current-vs-target.md)  
> **0-5 로드맵:** [docs/design/STAGE-0-5-implementation-roadmap.md](docs/design/STAGE-0-5-implementation-roadmap.md)  
> **진행 규칙:** [docs/design/PROCESS.md](docs/design/PROCESS.md)  
> 저장소: [github.com/gjtuc/link](https://github.com/gjtuc/link)

---

## 핵심 철학

| 원칙 | 설명 |
|------|------|
| **압축 ≠ 분해** | document ingest는 요약 없이 원문 청크 (STAGE 0-1 β-1) |
| 서술 제거 | 감정·평가·전망은 Pydantic 스키마에 슬롯이 없음 |
| 인과 ≠ 상관 | LLM 내러티브가 아니라 **코드화된 규칙(R01~R11)** 으로만 판정 |
| provenance | extracted / inferred / promoted / dropped — **검증·가설·기각 숨기지 않음** (STAGE 0-1 δ) |
| 최소 영속화 | Weaver는 검증 엣지 endpoint 중심 (8단계에서 orphan 정책 확장 예정) |

---

## 파이프라인 흐름

```
완성품(서술·논문·보고서) — STAGE 0-1: document ingest, 청크
    │
    ▼
[Deconstruct]  LLM → FactList (subject + state_change)  ← 원인과 결과 crumb
    │
    ▼
[Verify]       is_atomic=True → completed_facts / False → 재분해 대기
    │
    ├── (non-atomic & depth < cap) ──► Deconstruct 루프
    │
    ▼
[Skeptic]      모든 fact 쌍에 규칙 엔진 적용 → verified_edges / rejected
    │
    ▼
[Weaver]       콘솔 출력 또는 Neo4j MERGE (--db)
    │
    ▼
[Viz]          --db 시 graph_output.html 생성 + 브라우저 자동 오픈
```

---

## 요구 사항

- **Python** 3.11+ 권장
- **LLM API** — Google Gemini(권장) 또는 OpenAI
- **Neo4j** — `--db` 사용 시 (Neo4j Desktop 로컬 `bolt://localhost:7687` 등)

---

## 다른 PC에서 설치 (처음 한 번)

### 1. 클론

```bash
git clone https://github.com/gjtuc/link.git
cd link
```

### 2. 가상환경 & 의존성

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 비밀 설정 (API 키·Neo4j)

```bash
cp deconstructor/local_settings.example.py deconstructor/local_settings.py
```

`deconstructor/local_settings.py` 를 열어 아래를 채운 뒤 **저장(Ctrl+S)**:

```python
GEMINI_API_KEY = "your-key"
LLM_PROVIDER = "gemini"

# 상황별 모델 (API model code)
GEMINI_MODEL_FLASH = "gemini-3.5-flash"          # 빠른 작업: 이미지 OCR
GEMINI_MODEL_PRO = "gemini-3.1-pro-preview"      # 깊은 추론: 분해·요약·검증
GEMINI_THINKING_LEVEL_FLASH = "medium"           # minimal | low | medium | high
GEMINI_THINKING_LEVEL_PRO = "high"               # Pro는 high 권장 (thinking 시간↑)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-neo4j-password"
```

> `local_settings.py`는 `.gitignore` 대상입니다. **절대 커밋하지 마세요.**

대안: 프로젝트 루트에 `.env` 파일 사용 가능 (`python-dotenv`).

### Gemini 모델 이원화 (Flash vs Pro)

| tier | 기본 모델 | thinking | 쓰는 곳 |
|------|-----------|----------|---------|
| **Flash** | `gemini-3.5-flash` | `medium` | 이미지 OCR, 짧은 추출 |
| **Pro** | `gemini-3.1-pro-preview` | `high` | Deconstruct, URL/PDF 요약, Dreamer, Fact-Checker, Skeptic mechanism |

코드: `get_chat_model(tier="pro")` (파이프라인 기본) / `get_chat_model(tier="flash")` (웹 UI 이미지)

| 변수 | 설명 |
|------|------|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini API 키 |
| `GEMINI_MODEL_FLASH` | Flash model code (속도) |
| `GEMINI_MODEL_PRO` | Pro model code (추론) |
| `GEMINI_THINKING_LEVEL_FLASH` | Flash thinking: `minimal`~`high` |
| `GEMINI_THINKING_LEVEL_PRO` | Pro thinking: `high` 권장 |
| `OPENAI_API_KEY` | OpenAI 대안 |
| `LLM_PROVIDER` | `auto` \| `gemini` \| `openai` |
| `NEO4J_URI` | Bolt URI |
| `NEO4J_PASSWORD` | Neo4j 비밀번호 |

### 4. 사전 점검

```bash
python scripts/preflight_live.py
```

LLM 클라이언트·Neo4j 연결 상태를 확인합니다.

### 5. Neo4j (선택, `--db` 사용 시)

1. [Neo4j Desktop](https://neo4j.com/download/) 설치
2. 로컬 DB 생성, 비밀번호 설정
3. `bolt://localhost:7687` 로 기동

---

## 사용법

### 라이브 실행 (LLM + 리포트)

```bash
python main.py "A공장 정전 뉴스 헤드라인 텍스트"
```

### Neo4j 저장 + 인터랙티브 그래프 자동 오픈

```bash
python main.py "[단독] 10:00 grid power가 off됐다. 10:02 factory A power supply가 interrupted됐다." --db
```

- 검증된 인과만 Neo4j `:Fact` / `:CAUSES` 로 MERGE
- 종료 직후 `graph_output.html` 생성 → 기본 브라우저에서 pyvis 그래프 오픈
- 노드 hover: `subject`, `state_change`, `timestamp` / 드래그 시 물리 엔진 적용

### Dry-run (LLM 없음, 테스트·CI)

```bash
python main.py --dry-run
python main.py --dry-run "B발전소 화재"
python main.py --dry-run --db    # stub + Neo4j + viz
```

### JSON 출력

```bash
python main.py "헤드라인" --json
```

### Skeptic 규칙만 데모

```bash
python main.py --skeptic-only
```

---

## CLI 옵션 요약

| 옵션 | 설명 |
|------|------|
| `event` | 분석할 헤드라인 (생략 시 모드별 기본값) |
| `--dry-run` | Stub decomposer, LLM 호출 없음 |
| `--depth-cap` | 분해 깊이 상한 시나리오 (dry-run) |
| `--db` | Neo4j 영속화 + 파이프라인 후 그래프 시각화 |
| `--json` | 최종 상태 JSON 출력 |
| `--skeptic-only` | 인과 규칙 엔진 단독 데모 |

---

## 프로젝트 구조

```
link/
├── main.py                 # CLI 진입점
├── requirements.txt
├── scripts/
│   └── preflight_live.py   # LLM·Neo4j 사전 점검
├── test_run.py             # 스모크 테스트 (API 키 불필요)
├── test_skeptic_run.py     # Skeptic 스모크
├── deconstructor/
│   ├── config.py           # 설정 로드 (.env + local_settings)
│   ├── models.py           # AtomicFact, FactList, CausalEdge
│   ├── graph/builder.py    # LangGraph 컴파일·실행
│   ├── deconstruct/        # LLM 분해 노드
│   ├── verify/               # 원자성 분리
│   ├── routing/              # deconstruct 루프 vs skeptic 분기
│   ├── skeptic/              # 인과 규칙 엔진 (R01~R11)
│   ├── weaver/               # 콘솔 / Neo4j 영속화
│   ├── viz/                  # pyvis HTML + webbrowser
│   ├── cli/                  # argparse, live/dry 모드
│   ├── report/               # 터미널 리포트
│   └── llm/                  # Gemini / OpenAI
└── tests/                    # pytest (128+)
```

코드 내 상세 주석(한·영): `deconstructor/__init__.py` 에 아키텍처 요약.

---

## The Skeptic — 인과 규칙 (요약)

모든 atomic fact **쌍**에 대해 아래 규칙을 순서대로 평가합니다.

| Tier | 규칙 | 역할 |
|------|------|------|
| Identity | NoSelfLoop, DuplicatePair | 자기 루프·중복 쌍 거부 |
| Narrative | NarrativeLeak | 내러티브·평가 토큰 거부 |
| Temporal | TemporalOrder, Simultaneous, PostHocLag | 시간 순서·동시 상관 |
| Structural | CommonCause, CrossDomain, EntityChain | 공통 원인·도메인 격리 |
| Mechanism | Plausibility, ProposedMechanism | 전파 경로·기제 검증 |

`INCONCLUSIVE` 판정은 mechanism proposal + 재시도 경로가 있습니다 (`skeptic/retry/`).

---

## Neo4j 스키마

```cypher
(:Fact {
  id, subject, state_change, timestamp, trigger_event, is_atomic
})
(:Fact)-[:CAUSES { probability, latency }]->(:Fact)
```

Viz 모듈은 DB **전체** 그래프를 읽어 HTML로 렌더링합니다 (이전 실행 데이터 포함 가능).

---

## 테스트

```bash
# 전체 pytest (LLM·Neo4j 불필요)
python -m pytest tests/ -q

# 파이프라인 스모크 (14 phase)
python test_run.py

# Skeptic 스모크 (8 phase)
python test_skeptic_run.py
```

---

## 한·영 헤드라인 팁

- **순수 한국어** 주체만 있으면 `grid`/`power` 같은 전파 토큰이 없어 Mechanism·Isolation 규칙에서 거부될 수 있습니다.
- **한영 혼합** (`grid power`, `factory A power supply`) 이 인과 검증에 유리합니다.

예시 (검증 성공 사례):

```text
[단독] 10:00 grid power가 off됐다. 10:02 factory A power supply가 interrupted됐다.
당국, grid 정전이 공장 차단의 직접 원인이라 발표.
```

---

## 문제 해결

| 증상 | 조치 |
|------|------|
| `No LLM API key` | `local_settings.py` 저장 여부·키 확인 |
| Gemini 404 | model code 확인 — Flash `gemini-3.5-flash`, Pro `gemini-3.1-pro-preview` |
| Pro 느림 | 정상 — `GEMINI_THINKING_LEVEL_PRO=high` 는 thought 시간↑. Flash tier 는 OCR만 사용 |
| Neo4j 연결 실패 | Desktop 기동·비밀번호·`NEO4J_URI` 확인 |
| `[VIZ] could not open graph` | Neo4j up + `--db` + 노드 존재 여부 확인 |
| Windows 한글 깨짐 | `cli/print_util.py` cp949 폴백 적용됨 |

---

## 라이선스

연구·개인 사용 목적. 배포 시 라이선스 명시를 추가하세요.

---

## 변경 이력

- **v0.2.0** — LangGraph 파이프라인, Skeptic 규칙 엔진, Neo4j Weaver, pyvis 자동 시각화, 상세 코드 주석
