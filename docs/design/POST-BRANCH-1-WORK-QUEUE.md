# POST-BRANCH-1 작업 큐 (임시)

> ⚠️ **수명:** Branch-1 클로저 **이후** 착수. **큐 항목 전부 완료 시 이 파일 삭제** + git commit.  
> **지금 작업자에게 붙이지 마세요** — quota·`branch_1_complete=false` 동안은 대기.  
> **갱신:** 2026-06-20 — 감독 AI 채팅에서 확정·기록.

---

## 사용법 (감독 AI)

1. `git pull` 후 이 파일 확인
2. 선행 조건 충족 시 → 아래 **「작업자 복붙 블록」** 을 작업자 채팅에 전달
3. 완료 시 `[ ]` → `[x]`, E2E·pytest 증거 링크 한 줄 추가
4. **전 항목 [x]** → 이 파일 **삭제** 후 push

**선행 조건 (공통):** `branch_1_complete: true` (`scripts/branch1_full_e2e.py` exit 0)

---

## 큐 항목

### Q1 — 2-pass Dreamer (양끝 + Gap)

- [x] **상태:** 완료 (2026-06-22)
- **증거:** `pytest tests/test_q1_pass2_inputs.py tests/test_q1_two_pass_dry_run.py` + `phase_r_regression.py` exit 0 — PR `feat/stage0-sprint0-7`

---

### Q2 — 능력·한계 카드 + 업로드 전 경고

- [ ] **상태:** 미착수
- **사용자 결정:** branch/E2E 기록을 UI로 번역; **감독 AI 말투** `human_line`; 업로드 전 경고 ✅; probe 로그 git push.

<details>
<summary>작업자 복붙 블록 (Branch-1 후)</summary>

```markdown
Link POST-Branch-1 — capabilities + pre-upload warnings + run logs

1) branch_state + E2E RECORD + ingest_manifest → capabilities.json
2) 각 항목 human_line (감독 AI 말투 1문장) — UI·업로드 경고
3) 실행 전: verified / untested / unsupported → [그래도 실행][나중에]
4) probe/E2E마다 logs/capability_runs/YYYYMMDD-HHMM-<id>.json (exit, script, human_line) — push 가능
5) /api/capabilities 또는 /api/status 확장; pytest로 JSON 스키마 고정
6) 부하 후보 catalog (형식·개수·환경) — AI가 READ할 JSON/코드, md 남발 금지

금지: branch_1_complete 수동 true, Branch-2/3/STAGE-1 선행
```

</details>

---

### Q3 — 부하 테스트 AI 제안 (Q2와 함께 또는 직후)

- [ ] **상태:** 미착수
- **내용:** 사용자가 생각 못 할 probe 사례를 catalog로 유지; UI 「아직 안 해본 테스트 N가지」.

**예시 후보 (catalog 시드):**

| human_line (예) | 유형 |
|-----------------|------|
| PDF 3개 동시 업로드 | 개수 |
| `.opju` / Origin 프로젝트 파일 | 미지원 형식 |
| 스캔 PDF·표만 있는 PDF | 내용 |
| 10MB+ 단일 파일 | 크기 |
| Neo4j 꺼진 상태 실행 | 환경 |
| Gemini quota 429 | 환경 |

→ Q2 구현 시 `capabilities` catalog에 포함 권장.

---

## 완료 체크

| ID | 완료일 | 증거 (pytest / E2E / PR) |
|----|--------|--------------------------|
| Q1 | 2026-06-22 | `test_q1_pass2_inputs` (7) + `test_q1_two_pass_dry_run` + `phase_r_regression` exit 0 |
| Q2 | | |
| Q3 | | |

**전부 완료 시:** 이 파일 삭제 → `git commit -m "chore: remove POST-BRANCH-1-WORK-QUEUE (all items done)"`
