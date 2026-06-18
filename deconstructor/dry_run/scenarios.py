"""Built-in headline scenarios for matrix dry-run testing.
매트릭스 드라이런 테스트용 내장 헤드라인 시나리오.

Purpose / 목적
--------------
``HEADLINE_SCENARIOS`` and ``DEPTH_CAP_SCENARIO`` bundle headlines with
**expected** parse subjects, recursion caps, null-floor expectations, and
expected LangGraph step counts for parametrized tests.
``HEADLINE_SCENARIOS``·``DEPTH_CAP_SCENARIO``에 헤드라인과 **기대** 주어,
재귀 상한, null-floor 여부, 노드 스텝 수를 묶어 parametrized 테스트 지원.

Pipeline position / 파이프라인 위치
-----------------------------------
Consumed by test matrix and CLI examples — not read by graph at runtime except
via chosen headline string passed as ``raw_text``.
테스트 매트릭스·CLI 예제용; 런타임 그래프는 ``raw_text``로 넘긴 헤드라인만 사용.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- ``expect_node_steps`` must match ``build_graph`` routing for stub facts — update
  when graph topology changes.
- ``DEPTH_CAP_SCENARIO`` uses low ``max_recursion_depth=2`` to force partial run.
- 그래프 토폴로지 변경 시 ``expect_node_steps`` 재검증.
- ``DEPTH_CAP_SCENARIO``는 ``max_recursion_depth=2``로 partial 강제.
"""

from __future__ import annotations

from dataclasses import dataclass

from deconstructor.dry_run.modes import DEPTH_CAP_PREFIX


@dataclass(frozen=True)
class HeadlineScenario:
    """One test headline with expected parse + pipeline outcomes.
    파싱·파이프라인 기대 결과가 붙은 테스트 헤드라인 1건."""

    headline: str
    expected_subject: str
    label: str
    max_recursion_depth: int = 5
    expect_null_floor: bool = True
    expect_node_steps: int = 5


HEADLINE_SCENARIOS: tuple[HeadlineScenario, ...] = (
    HeadlineScenario("A공장 정전", "A공장", "korean_outage"),
    HeadlineScenario("B발전소 화재", "B발전소", "korean_fire"),
    HeadlineScenario("Plant C outage", "Plant C", "english_outage"),
    HeadlineScenario("Line-D shutdown", "Line-D", "english_shutdown"),
)

# Exercises partial_run + INCOMPLETE status (never reaches null floor).
# partial_run + INCOMPLETE 상태 검증 (null floor 미도달).
DEPTH_CAP_SCENARIO = HeadlineScenario(
    headline=f"{DEPTH_CAP_PREFIX}Z공장 정전",
    expected_subject="Z공장",
    label="depth_cap_exhaustion",
    max_recursion_depth=2,
    expect_null_floor=False,
    expect_node_steps=5,
)

DEFAULT_HEADLINE = HEADLINE_SCENARIOS[0].headline
