# Link — 감독·통역 AI 인수인계 (새 채팅용)

> **갱신:** 2026-06-20  
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

## 4. 현재 상태 (2026-06 — quota 대기)

### 끝난 것

| 항목 | 증거 |
|------|------|
| Branch-0 — Phase R(읽기) | `python scripts/phase_r_regression.py` exit 0 |
| `verify_read()` / S1-READ | 읽기 실패 시 LLM 0회 |
| Sprint 0~7 구현 | PR #1 `feat/stage0-sprint0-7` |
| S0-A PDF full E2E | [`S0-A-E2E-RECORD.md`](S0-A-E2E-RECORD.md) |
| Branch 게이트 | `tests/test_branch_gates.py` — Branch-2/3/STAGE-1 spec 생성 시 fail |

### `branch_state.json` (수동 true 금지)

```json
{
  "branch_0": "active",
  "branch_1_complete": false,
  "branch_2_unlocked": false
}
```

### 막힌 것 (코드 문제 아님)

- **Branch-1** — S0-B·S0-C **Phase A full** (Gemini 필요)
- **Gemini API 일일 한도(RPD) 소진** — 2026-06-18 근처 daily limit
- 리셋: 보통 **다음날(UTC-8)** 또는 24h 후

### 지금 할 일 (감독·작업자·사용자)

**추가 작업 없음 (대기).** ingest 안 건드리면 regression도 불필요.  
사용자가 **「Branch-1 실행」** 할 때만:

```bash
python scripts/phase_r_regression.py   # 선행, exit 0
python scripts/branch1_full_e2e.py
```

성공 시: `branch_1_complete: true` (스크립트가 갱신). `branch_2_unlocked`는 **false 유지**.

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
| **이 감독 채팅에서 작업자가 한 일** | **없음** (논의·설계만) |
| **작업자 지금 할 일** | **없음** — quota·Branch-1 대기 |
| **금지** | Branch-2/3/STAGE-1 spec, `branch_1_complete` 수동 true, ingest 수정 없이 regression 스킵 |
| **다음 본공사** | 사용자 「Branch-1 실행」→ `branch1_full_e2e.py` |
| **그 다음 (큐)** | `POST-BRANCH-1-WORK-QUEUE.md` — Branch-1 **이후** 분기 |

### 작업자 명령 치트시트

| 상황 | 명령 |
|------|------|
| ingest 수정 후 | `python scripts/phase_r_regression.py` |
| quota 후 Branch-1 | `python scripts/branch1_full_e2e.py` |
| 잠금 확인 | `pytest tests/test_branch_gates.py` |

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

현재: Branch-0 ✅, Branch-1 quota 대기, branch_1_complete=false.
지금 할 일 없음. 「Branch-1 실행」 때만 branch1_full_e2e.py.

임시 큐는 작업 완료 후 삭제. 매 답변: 풀어설명 + 작업자 복붙블록 + 지금 할 일(있/없).
```

---

## 10. Branch-1 성공 후

사용자가 결과 붙이면: 통역 + 다음 주문문.  
2a/2b/3 unlock은 `branch_state`·RECORD·pytest 기준. md 확장 주문 금지 unless 테스트 필요.
