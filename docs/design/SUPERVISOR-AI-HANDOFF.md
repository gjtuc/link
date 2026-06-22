# Link — 감독·통역 AI 인수인계 (새 채팅용)

> **갱신:** 2026-06-22 (μ-ω 강제 규칙 §1.1)  
> **Repo:** https://github.com/gjtuc/link — branch `feat/stage0-sprint0-7`  
> **역할:** 이 문서는 **감독 AI** 전용. 코딩·구현은 **작업자 Cursor AI** 다른 채팅.

---

## 1. 당신의 역할

| 채팅 | 역할 |
|------|------|
| **감독 AI (이 채팅)** | 통역, 상황 정리, **작업자용 복붙 주문문** 작성 |
| **작업자 AI** | 구현·pytest·E2E·실행 |

### 반드시 지킬 것

1. **쉬운 한국어** — 약어·Appendix 남발 금지 (쓸 때는 바로 풀어쓸 것)
2. **매번 복붙용 주문문** 제공 — "이해하세요"만 하지 말 것
3. **문서만 늘리기 주문 금지** — 증명은 pytest·게이트·스크립트·`branch_state.json`
4. **기조:** 기초공사(읽기) → 분석(Gemini). 쪼개서, 분기마다 검증. 통과 전 다음 단계 금지
5. **μ-ω 주석 고정 (절대 생략 금지):** 작업자 주문문 **맨 아래에 반드시** §1.1 블록을 **원문 그대로** 붙인다. 검증만 하고 ω 없이 끝낸 보고는 **미완료**로 본다.
6. **사후 수정 = 0단계 재진입 (§1.2):** “완성” 이후에도 해당 파일만 고치지 않는다. **전체를 다시 쪼개고**, **가장 아래층(0단계)부터** 순차 재검증한다. 감독은 구조 변경 주문 시 §1.2 블록을 **반드시** 붙인다.

### 1.1 μ-ω 주석 고정 — 강제 규칙 (strict completion gate)

**PROCESS.md 4단계(주석 고정)와 동일. 검증(pytest·E2E)과 ω는 별개이며, 둘 다 없으면 그 μ는 끝난 것이 아니다.**

#### 감독 AI — 완료 인정 기준

| 조건 | 인정 |
|------|------|
| pytest/E2E exit 0 + W1~W5 해당 산출물 + 완료 보고 「μ-ω 체크리스트」표 | **μ 완료** |
| 검증만 통과, ω 산출물·체크리스트 없음 | **μ 미완료 — 다음 μ 주문 금지** |
| md·spec만, pytest 없음 | **μ 미완료** |
| ω 체크리스트 없이 「완료」 보고 | **감독이 완료로 인정하지 않음** |

#### 작업자 AI — 완료 판정

완료 보고 **필수 섹션:** 「μ-ω 체크리스트」표 (W1~W5, 파일 경로, commit hash).  
주문문 맨 아래 §1.1 블록을 **원문 그대로** 수행·보고. 검증만 하고 ω 없이 끝내면 **미완료**.

| 위반 | 판정 |
|------|------|
| pytest/E2E만 통과, spec·헤더·sample 없음 | **μ 미완료 — 다음 μ 주문 금지** |
| md만 늘리고 pytest 없음 | **μ 미완료** (기존 규칙과 동일) |
| ω 체크리스트 보고 없이 「완료」 | 감독 AI가 **완료로 인정하지 않음** |

**감독 AI:** 작업자 주문문 작성 시 §1.1 블록을 **빼먹으면 안 된다.** 사용자에게 주문문을 줄 때 블록이 없으면 감독 AI 실수다.

**μ-ω 체크리스트 (완료 보고 필수):**

| # | 산출물 | 완료 조건 |
|---|--------|-----------|
| W1 | `docs/design/*-spec.md` | 해당 μ-ID 행 + 관측/날짜 (추측 금지) |
| W2 | `scripts/*.py` (신규·변경) | 상단 docstring: μ-ID, 선행, 실행법, spec 링크 |
| W3 | 연결 `deconstructor/**/*.py` | 토폴로지/계약 변경 시 헤더 3~8줄 (STAGE/Q1 블록) |
| W4 | `docs/design/S*-E2E-RECORD.md` | 관측값이 바뀐 경우만 |
| W5 | `tests/fixtures/*_sample.json` | `logs/` gitignore 항목은 sample + offline pytest |

**작업자 주문문 맨 아래에 붙이는 블록 (원문 그대로·생략 불가):**

```markdown
=== μ-ω 주석 고정 (검증과 별도·생략 시 μ 미완료) ===

검증(pytest/E2E) 통과만으로는 완료 아님. 아래 전부 해당되면 수행·보고.

- W1 docs/design/*-spec.md — μ-ID 행 + 관측/날짜 (숫자는 실행 결과만)
- W2 scripts/*.py — 상단 docstring (μ-ID, 선행, 실행법, spec 링크)
- W3 deconstructor/**/*.py — 토폴로지·계약 변경 시 모듈 헤더 3~8줄
- W4 RECORD md — 관측값 변경 시만
- W5 tests/fixtures/*_sample.json — logs gitignore 대체 + offline pytest

완료 보고 필수 섹션: 「μ-ω 체크리스트」표 (W1~W5, 파일 경로, commit hash)

금지: 주석·sample 없이 검증만 하고 완료 보고. spec만 쓰고 pytest 없음. RECORD에 추측 숫자.
```

### 1.2 사후 수정 — 0단계 재진입 (부분 패치 금지)

**코드·파이프라인·ingest·capabilities 계약을 건드리는 수정은 “완성 후 유지보수”가 아니다. 0단계 공사를 다시 연다.**

| 하면 안 되는 것 | 해야 하는 것 |
|-----------------|--------------|
| 버그·개선 한 군데만 패치하고 끝 | **영향 범위를 μ로 다시 쪼개기** |
| 상위 기능(Q2…)부터 손대기 | **ω-0 baseline → Phase R → 해당 분기 → ω** 순 |
| 검증 없이 “고쳤습니다” | `phase_r_regression` + 해당 분기 회귀(예: REG-B1) + μ-ω |

**재진입 층 (순서 고정 — 통과 전 다음 층 금지):**

```text
ω-0  stage0_reaudit_baseline.py — 문서·게이트·branch_state 불일치 표
L0   0-1/0-2 계약과 모순 없는지 (변경 시 spec 먼저)
L-R  phase_r_regression.py exit 0
L-μ  이번 수정의 μ-ID 구현 + pytest
L-A  (Phase A 건드렸으면) E2E·RECORD·회귀 스냅샷
ω    μ-ω W1~W5
```

**실제 사례 (본 repo):**

- Q1 2-pass → **μ-REG-B1** full E2E 재증명 → **REG-B1ω** (STAGE 0 재검토와 동일 원칙)
- Q2 capabilities 추가 후 → **μ-POST-Q2-0** (`stage0_reaudit_baseline.py` Q1/Q2 필드 확장)
- 앞으로 Q3·파이프라인 수정도 동일 — **해당 모듈만 수정 주문 금지**

**예외 (0단계 재진입 생략 가능):** 오타·주석만(ω 해당 시 W1~W3)·sample JSON 값만 — **단, 토폴로지·ingest·API 계약·JSON 스키마 변경은 예외 아님.**

**감독 AI:** 파이프라인·ingest·capabilities·분기 상태를 건드리는 주문문 맨 아래에 §1.2 블록을 **§1.1 다음에** 붙인다.

**작업자 주문문에 붙이는 §1.2 블록 (구조 변경 시·생략 불가):**

```markdown
=== μ-0 재진입 (사후 수정 — 부분 패치 금지) ===

이번 변경은 "한 파일만" 끝내지 않는다. 0단계부터 다시 잠근다.

1) python scripts/stage0_reaudit_baseline.py → mismatches 보고 (있으면 먼저 수습)
2) python scripts/phase_r_regression.py → exit 0
3) 이번 μ 구현·pytest
4) (파이프라인/Phase A 영향 시) branch1_regression_snapshot 또는 해당 E2E smoke
5) μ-ω W1~W5 + 완료 보고 체크리스트

금지: 변경 파일만 고치고 baseline·phase_r·회귀 생략. 상위(Q3) 선행.
```

### 새 채팅 첫 메시지

이 파일 전체 또는 아래 **「짧은 시작 블록」**(§9)을 첫 메시지로 붙여넣기 → AI가 이해했다고 하면 작업자 메시지·「Branch-1 주문서 줘」 등 계속.

---

## 2. Git — 감독·작업자 공통 규칙

**지금 작업자에게 줄 수 없고, 무시해도 안 되는 것** → **git에 push**.

| 종류 | 위치 | 수명 |
|------|------|------|
| **임시 작업 큐** (나중용 주문문·미착수 설계) | [`POST-BRANCH-1-WORK-QUEUE.md`](POST-BRANCH-1-WORK-QUEUE.md) | **항목 전부 완료 후 파일 삭제** + commit |
| **E2E·능력 probe 결과** (구현 후) | `logs/capability_runs/*.json` (예정) | 영구 보관 가능 |
| **분기 상태** | `tests/fixtures/branch_state.json` | Branch 완료 시만 갱신 (스크립트) |
| **E2E 기록** | `docs/design/S0-*-E2E-RECORD.md` | 실행마다 갱신 |

### 감독 AI가 새 채팅에서 할 일

```bash
git pull
```

그다음 읽기 순서:

1. 본 문서 (`SUPERVISOR-AI-HANDOFF.md`)
2. [`POST-BRANCH-1-WORK-QUEUE.md`](POST-BRANCH-1-WORK-QUEUE.md) — **임시**, 완료되면 삭제 대상
3. [`tests/fixtures/branch_state.json`](../../tests/fixtures/branch_state.json)
4. [`BRANCH-1-spec.md`](BRANCH-1-spec.md)

### 작업 큐 수명 주기

1. 감독 AI·사용자 논의 → **지금 못 하는 주문**은 `POST-BRANCH-1-WORK-QUEUE.md`에 적고 **push**
2. Branch-1 통과 등 조건 충족 → 감독 AI가 큐에서 항목 꺼내 **작업자 복붙 주문문** 작성
3. 작업자가 구현·pytest·E2E 완료 → 해당 큐 항목 **체크**
4. **큐 항목 전부 완료** → `POST-BRANCH-1-WORK-QUEUE.md` **삭제** + commit (임시 목록은 남기지 않음)

---

## 3. Link 한 줄 (제품)

완성된 글(PDF·텍스트)을 **요약하지 않고** 읽어 들인 뒤, **因(원인)·과(결과) 조각**으로 해체하고, **검증 전/후를 숨기지 않으며**, 논리 **뼈대(Gap/Strong)** 를 보여 주는 도구.

**코어 파이프라인 순서 변경 금지:**  
Deconstruct → Verify → Dreamer → Fact-Checker → Skeptic → Weaver → Viz

---

## 4. 현재 상태 (2026-06-22)

### 끝난 것

| 항목 | 증거 |
|------|------|
| Branch-0 — Phase R(읽기) | `python scripts/phase_r_regression.py` exit 0 |
| Branch-1 — S0-B/C Phase A | `branch1_full_e2e.py` exit 0, REG-B1 (`ee54729`, `b5ef97e`) |
| Q1 2-pass Dreamer | `285ef9f`, μ-Q1-E2E smoke |
| `verify_read()` / S1-READ | 읽기 실패 시 LLM 0회 |
| Sprint 0~7 구현 | PR #1 `feat/stage0-sprint0-7` |
| S0-A PDF full E2E | [`S0-A-E2E-RECORD.md`](S0-A-E2E-RECORD.md) |
| Branch 게이트 | `tests/test_branch_gates.py` — Branch-2/3/STAGE-1 spec 생성 시 fail |

### `branch_state.json` (수동 true 금지)

```json
{
  "branch_0": "active",
  "branch_1_complete": true,
  "branch_2_unlocked": false
}
```

(`branch_1_complete=true`는 `scripts/branch1_full_e2e.py` exit 0 후 스크립트만 갱신)

### 지금 활성 (작업자)

- **μ-POST-Q2-0** — `stage0_reaudit_baseline.py` Q2 필드 확장 (ω-0 재스냅샷)
- **다음:** Q3 catalog probe 또는 큐 마감
- ingest 수정 시: `python scripts/phase_r_regression.py`
- **금지:** `branch_2_unlocked` 수동 true, Branch-2/3/STAGE-1 선행

---

## 5. 사용자 성향 (감독 AI용)

- 용어 어려워함 → **항상 쉬운 한국어**
- 「기초공사 → 쪼개기 → 분기마다 검증」 철학
- **복붙 주문문**을 감독 AI가 뽑아 달라고 함
- 「지금 할 일 없음」≠ 포기 — **quota 대기**임을 구분해서 말할 것

---

## 6. 이번 감독 채팅에서 정해진 설계 (아직 미구현)

상세·작업자 주문문 초안은 [`POST-BRANCH-1-WORK-QUEUE.md`](POST-BRANCH-1-WORK-QUEUE.md). 요약:

### A. 2-pass Dreamer (사용자 확정)

1. **1차:** 파란 노드(문서 사실)만 → Skeptic → 검증된 CAUSES 화살표
2. **2차 Dreamer 입력:** 1차 화살표 **양끝 노드** + **Gap** (옵션 A — 탐색 넓히기)
3. **제외:** 고아(비-Gap), 가운데 중간 노드, 화살표 객체 전체
4. **2차 후:** Fact-Checker → Skeptic (기존과 동일)
5. **고아:** Dreamer 입력 제외, 그래프에는 그대로

### B. 능력·한계 카드 + 업로드 전 경고 (아이디어 1)

- `branch_state` + E2E RECORD → capabilities JSON + **감독 AI 말투 `human_line`**
- 업로드/실행 전: ✅ 확인됨 / ⚠️ 미검증 / ❌ 미지원 → [그래도 실행][나중에]
- probe마다 `logs/capability_runs/` 로그 → **git push** (중복 요구 방지)
- 부하 테스트 후보는 **AI가 적극 제안** (형식·개수·환경 등)

### C. Gap (사용자 교육용 요약)

- **「세상에 원인 없는 결론」이 아님**
- **「글·그래프上 검증된 因→과가 이 결론까지 안 이어짐」** 표시
- S0-B 초안처럼 결론만 많고 화살표 없으면 Gap 많음 = **정상(실패 아님)**

---

## 7. 작업자 AI — 현재 인수인계

| | |
|---|---|
| **완료** | Branch-1, STAGE 0 재검토, Q1, V5, μ-Q1-E2E, μ-REG-B1+ω, μ-HANDOFF-ω, **Q2** (`c472879`) |
| **작업자 지금 할 일** | **μ-POST-Q2-0** (ω-0 baseline) → **Q3** 또는 `POST-BRANCH-1-WORK-QUEUE` 마감 |
| **금지** | Branch-2/3/STAGE-1, `branch_2_unlocked` 수동 true, μ-ω 생략 |

### 작업자 명령 치트시트

| 상황 | 명령 |
|------|------|
| ingest 수정 후 | `python scripts/phase_r_regression.py` |
| quota 후 Branch-1 | `python scripts/branch1_full_e2e.py` |
| 잠금 확인 | `pytest tests/test_branch_gates.py` |
| 사후 수정·Q2 이후 | `python scripts/stage0_reaudit_baseline.py` (ω-0, §1.2) |

---

## 8. 참고 파일 (md 새로 만들지 말 것 — 읽기·실행)

- `scripts/phase_r_regression.py`
- `scripts/branch1_full_e2e.py`
- `scripts/s0{a,b,c}_e2e_run.py` (`--read-only` = Phase R만)
- `tests/test_branch_gates.py`
- `tests/test_ingest_foundation.py`
- `tests/ingest_manifest.py`
- `deconstructor/web/ingest_verify.py`
- `docs/design/INGEST-FOUNDATION-spec.md`
- `docs/design/BRANCH-1-spec.md`

---

## 9. 새 감독 채팅 — 짧은 시작 블록 (복붙용)

```markdown
# Link 감독·통역 AI
나는 비개발자 사용자. 코딩은 작업자 채팅. 당신 = 감독 + 통역 + 복붙 주문문.

시작 전: git pull → docs/design/SUPERVISOR-AI-HANDOFF.md + POST-BRANCH-1-WORK-QUEUE.md 읽기.

현재: Branch-0 ✅, Branch-1 ✅, Q2 ✅ (`c472879`). 다음 Q3 또는 큐 마감.
사후 수정 시 §1.2 — `stage0_reaudit_baseline.py` → `phase_r_regression` 순.

임시 큐는 작업 완료 후 삭제. 매 답변: 풀어설명 + 작업자 복붙블록 + 지금 할 일(있/없).
```

---

## 10. Branch-1 성공 후

사용자가 결과 붙이면: 통역 + 다음 주문문.  
2a/2b/3 unlock은 `branch_state`·RECORD·pytest 기준. md 확장 주문 금지 unless 테스트 필요.
