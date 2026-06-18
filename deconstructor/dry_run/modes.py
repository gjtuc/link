"""Dry-run headline prefixes and scenario mode detection.
드라이런 헤드라인 접두사 및 시나리오 모드 판별.

Purpose / 목적
--------------
``DEPTH_CAP_PREFIX`` marks headlines that exercise **infinite refinement**
stub behavior (compound crumb replaced by compound crumb until cap).
``DEPTH_CAP_PREFIX``는 **무한 정제** 스텁(복합→복합 반복 후 상한 절단) 시나리오 표시.

Pipeline position / 파이프라인 위치
-----------------------------------
::

    headline --> is_depth_cap_headline / strip_dryrun_prefix
        --> stub_decompose routing

Control plane only — does not appear in final report INPUT after strip.
제어 평면; strip 후 리포트 INPUT에는 접두사 미포함.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Prefix must stay ASCII and colon-terminated for easy ``startswith`` checks.
- Add new modes as new constants + ``is_*`` / ``strip_*`` pairs, not ad-hoc strings.
- 접두사는 ASCII·콜론 종료 유지; 새 모드는 상수+함수 쌍으로 추가.
"""

from __future__ import annotations

DEPTH_CAP_PREFIX = "DRYRUN:DEPTH_CAP:"


def is_depth_cap_headline(headline: str) -> bool:
    """True when headline triggers the stuck-decomposition stub.
    stuck-decomposition 스텁을 쓰는 헤드라인이면 True."""
    return headline.strip().startswith(DEPTH_CAP_PREFIX)


def strip_dryrun_prefix(headline: str) -> str:
    """Remove dry-run control prefix; return bare headline for parsing.
    드라이런 제어 접두 제거 후 파싱용 순수 헤드라인 반환."""
    text = headline.strip()
    if text.startswith(DEPTH_CAP_PREFIX):
        return text[len(DEPTH_CAP_PREFIX) :].strip()
    return text
