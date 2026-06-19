"""
Mechanism proposals for INCONCLUSIVE retry.
INCONCLUSIVE 재시도용 메커니즘 제안 패키지.

Purpose / 목적
--------------
Bridge retry orchestration to stub/LLM mechanism fill implementations.
재시도 오케스트레이션과 스텁/LLM 메커니즘 채우기 구현을 연결한다.

Pipeline position / 파이프라인 위치
---------------------------------
  retry.orchestrate  →  fill_mechanisms  →  engine.evaluate_batch(mechanisms=…)

When to modify / 수정 시점
--------------------------
- ``proposals_for_inconclusive`` is a backward-compatible alias for stub path.
- Export new public APIs via ``__all__`` only.

Key invariants / 핵심 불변조건
------------------------------
- Only INCONCLUSIVE rejections receive proposals in fill.py.
"""

from deconstructor.skeptic.mechanism_proposal.fill import (
    fill_mechanisms,
    proposals_for_inconclusive_stub,
    proposals_to_mechanism_map,
)
from deconstructor.skeptic.mechanism_proposal.llm import (
    invoke_mechanism_proposal,
    propose_mechanisms_llm,
)
from deconstructor.skeptic.mechanism_proposal.schemas import (
    MechanismProposal,
    MechanismProposalBatch,
)
from deconstructor.skeptic.mechanism_proposal.stub import stub_mechanism

# Backward-compatible alias — older imports use this name for stub-only path.
proposals_for_inconclusive = proposals_for_inconclusive_stub

__all__ = [
    "MechanismProposal",
    "MechanismProposalBatch",
    "fill_mechanisms",
    "invoke_mechanism_proposal",
    "propose_mechanisms_llm",
    "proposals_for_inconclusive",
    "proposals_for_inconclusive_stub",
    "proposals_to_mechanism_map",
    "stub_mechanism",
]

