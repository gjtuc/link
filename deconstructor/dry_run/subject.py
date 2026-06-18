"""Parse bare subject tokens from one-line facility headlines.
한 줄 시설 헤드라인에서 주어(엔티티) 토큰 추출.

Purpose / 목적
--------------
``parse_subject`` strips dry-run control prefixes and event suffixes
(Korean/English outage, fire, etc.) to recover the physical entity name used
in stub ``AtomicFact.subject`` fields.
드라이런 제어 접두·사건 접미사(정전, fire 등)를 제거해 스텁
``AtomicFact.subject``에 쓸 물리 엔티티명 복원.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    raw headline --> strip_dryrun_prefix (modes.py)
        --> parse_subject --> stub_decompose / HeadlineScenario.expected_subject

Used by stub passes and scenario tests; not used by live LLM deconstruct.
스텁·시나리오 테스트용; 라이브 LLM deconstruct에는 미사용.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Extend ``SUFFIXES`` tuple for new headline templates (longest match via endswith).
- Fallback ``"facility"`` when parsing yields empty — keeps stubs from crashing.
- Empty input after strip also returns ``"facility"``.
- 새 헤드라인 패턴은 ``SUFFIXES`` 확장; 빈 결과는 ``"facility"`` 폴백.
"""

from __future__ import annotations

from deconstructor.dry_run.modes import strip_dryrun_prefix

# Trailing event phrases stripped before taking subject (order: first match wins).
# 주어 추출 전 제거할 끝 접미사 (endswith 매칭, 먼저 맞는 것 사용).
SUFFIXES: tuple[str, ...] = (
    " 정전",
    " 화재",
    " 폭발",
    " 정지",
    " 가동중단",
    " outage",
    " fire",
    " explosion",
    " shutdown",
)


def parse_subject(headline: str) -> str:
    """
    Extract the physical entity from a surface headline.

    Examples:
        "A공장 정전"   -> "A공장"
        "Plant B fire" -> "Plant B"

    표면 헤드라인에서 물리 엔티티 추출.
    """
    text = strip_dryrun_prefix(headline).strip()
    if not text:
        return "facility"

    lowered = text.lower()
    for suffix in SUFFIXES:
        if lowered.endswith(suffix.lower()):
            subject = text[: -len(suffix)].strip()
            return subject or "facility"

    # No known suffix: first whitespace token (English headlines).
    # 알려진 접미사 없음: 첫 토큰 (영문 헤드라인).
    parts = text.split()
    return parts[0] if parts else "facility"
