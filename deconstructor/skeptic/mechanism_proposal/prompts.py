"""
LLM prompts for mechanism proposal.
메커니즘 제안용 LLM 프롬프트.

Purpose / 목적
--------------
Static system/user prompt strings for ``llm.build_mechanism_messages``.
Enforce mechanical, non-narrative one-sentence mechanisms referencing both crumbs.
``llm.build_mechanism_messages``용 정적 프롬프트.
기계적·비서술적 한 문장, 양쪽 크럼 참조 강제.

Pipeline position / 파이프라인 위치
---------------------------------
  mechanism_proposal.llm  →  **prompts** (imported constants)

When to modify / 수정 시점
--------------------------
- Keep aligned with ``MechanismProposal`` schema and R07 token validation.
- ``MECHANISM_USER`` format keys must match ``llm.py`` ``.format()`` call.
- R07 토큰 검증과 일치하도록 유지.

Key invariants / 핵심 불변조건
------------------------------
- No emotion/valuation/forecast language in system rules.
- User template exposes subject + state_change only (no raw fact ids to LLM).
"""

MECHANISM_SYSTEM = """You propose mechanical propagation paths between two atomic facts.

Rules:
- No emotion, valuation, or forecast language.
- Mechanism must reference BOTH source and target subjects or state changes.
- One sentence only.
"""

MECHANISM_USER = """Source fact:
  subject: {source_subject}
  state_change: {source_change}

Target fact:
  subject: {target_subject}
  state_change: {target_change}

Return a MechanismProposal with proposed_mechanism only."""

