# Link 설계·구현 진행 규칙

## 반복 절차 (0-1, 0-2, … 각 서브단계마다)

각 **0-N** 서브단계는 아래 순서를 **반드시** 따른다. 다음 서브단계(0-(N+1))로
넘어가기 **전에** 이전 단계 주석·문서화가 끝나야 한다.

```
1. 0-N  1차 작성   — 설계·요구·체크리스트
2. 0-N  재쪼개기   — 검증 가능한 원자(ID)로 분해 (α, β, …)
3. 0-N  점검·수정  — 모순·범위 과대·코드베이스 gap 반영
4. 0-N  주석 고정  — 본 문서 + 관련 코드 모듈 docstring/헤더 주석
5. 0-(N+1) 시작    — **직전 단계(0-N)의 재쪼개본·체크리스트·NON-GOALS** 를 입력으로 사용
6. (5 이후) 0-(N+1)에 대해 1→4 반복
```

## 주석 “고정”이란

- `docs/design/STAGE-0-N-*.md` 에 **완료본 + 재쪼개 ID + C-* 체크리스트** 기록
- 해당 단계와 직접 연결된 **코드 파일 상단**에 `STAGE 0-N` 블록 주석 (링크·요약)
- README 등 사용자-facing 문서는 **0-1 계약**과 충돌하지 않게 유지

## Sprint 구현 (0-5 이후)

0-5 Appendix A~ 각 Sprint도 **미니 0-N**:

```
Sprint N  스펙(Appendix) → SP* 작업 → 구현·테스트 → DoD(0-3 AC 갱신·주석)
```

상세: ``docs/design/STAGE-0-5-implementation-roadmap.md``

## 0단계 서브단계 목록 (예정)

| ID | 이름 | 문서 |
|----|------|------|
| 0-1 | 한 줄 정의·계약 | `STAGE-0-1-product-definition.md` ✅ |
| 0-2 | 사용자 시나리오 | `STAGE-0-2-user-scenarios.md` ✅ |
| 0-3 | 성공 기준 (Acceptance) | `STAGE-0-3-acceptance-criteria.md` ✅ |
| 0-4 | 현재 vs 목표 gap | `STAGE-0-4-current-vs-target.md` ✅ |
| 0-5 | 구현 로드맵 | `STAGE-0-5-implementation-roadmap.md` ✅ |
| Sprint 0+ | G-* 구현 | Appendix A~I ✅ — **0단계 Sprint 0~7 완료** |

## 코어 파이프라인 (변경 금지 방향)

Deconstruct → Verify(재귀) → Dreamer → Fact-Checker → Skeptic → Weaver → Viz

0단계는 **입력·조립·표현 계약** 을 고친다. 위 노드 역할 이름·순서는 유지한다.
