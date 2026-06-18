"""Pipeline trace datatypes — StepRecord and TracedRun containers.
파이프라인 추적 데이터 타입 — StepRecord·TracedRun 컨테이너.

Purpose / 목적
--------------
Lightweight dataclasses decoupling **trace capture** from report formatting
and JSON export. ``StepRecord`` holds one node firing; ``TracedRun`` bundles
final ``State`` plus ordered steps.
추적 수집을 리포트·JSON과 분리하는 경량 dataclass.
``StepRecord`` = 노드 1회; ``TracedRun`` = 최종 ``State`` + 순서 있는 steps.

Pipeline position / 파이프라인 위치
-----------------------------------
Produced by ``trace/runner.py``; consumed by ``report.compose`` and tests.
``trace/runner.py`` 생성 → ``report.compose``·테스트 소비.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Prefer optional count fields (``extracted_count``, etc.) for machine assertions;
  ``detail`` string is for humans only.
- ``node_sequence`` property avoids duplicating sequence logic in tests.
- 카운트 필드는 기계 검증용; ``detail``은 사람용.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deconstructor.pipeline.state import State


@dataclass
class StepRecord:
    """One node firing with a compact summary of its state delta.
    state delta 요약이 붙은 노드 1회 발화 기록."""

    step_index: int
    node: str
    recursion_depth: int | None = None
    extracted_count: int | None = None
    completed_count: int | None = None
    verified_edge_count: int | None = None
    detail: str = ""


@dataclass
class TracedRun:
    """Full pipeline result plus execution trace.
    전체 파이프라인 결과 + 실행 추적."""

    final_state: State
    steps: list[StepRecord] = field(default_factory=list)

    @property
    def node_sequence(self) -> list[str]:
        """Ordered node names for routing assertions in tests."""
        return [s.node for s in self.steps]
