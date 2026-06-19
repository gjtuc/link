"""
Step 1 — Provenance 타입 정의 (Micro-step S1-1)
==============================================

source_type: 팩트의 출처 신분 (3값만 허용)
check_status: 팩트체커·고스트 노드 상태 (Dreamer/FactChecker 연동용)

로그 prefix: [PROV-S1-1]
"""

from __future__ import annotations

import logging
from typing import Literal

logger = logging.getLogger(__name__)

SourceType = Literal["extracted", "inferred", "verified"]
CheckStatus = Literal["active", "pending", "promoted", "dropped"]

SOURCE_TYPES: frozenset[str] = frozenset({"extracted", "inferred", "verified"})
CHECK_STATUSES: frozenset[str] = frozenset({"active", "pending", "promoted", "dropped"})

DEFAULT_SOURCE_TYPE: SourceType = "extracted"
DEFAULT_CHECK_STATUS: CheckStatus = "active"


def _log(msg: str) -> None:
    line = f"[PROV-S1-1] {msg}"
    logger.info(line)
    print(line)


def validate_source_type(value: str) -> SourceType:
    """source_type 3값 외 입력 시 ValueError."""
    if value not in SOURCE_TYPES:
        _log(f"REJECT invalid source_type={value!r}")
        raise ValueError(
            f"source_type must be one of {sorted(SOURCE_TYPES)}, got {value!r}"
        )
    return value  # type: ignore[return-value]


def validate_check_status(value: str) -> CheckStatus:
    """check_status 4값 외 입력 시 ValueError."""
    if value not in CHECK_STATUSES:
        _log(f"REJECT invalid check_status={value!r}")
        raise ValueError(
            f"check_status must be one of {sorted(CHECK_STATUSES)}, got {value!r}"
        )
    return value  # type: ignore[return-value]


def is_ghost_dropped(source_type: str, check_status: str) -> bool:
    """A안: 검증 탈락 고스트 노드 (노란 점선 + ✖ + opacity)."""
    return source_type == "inferred" and check_status == "dropped"


def is_promoted_inferred(source_type: str, check_status: str) -> bool:
    """Dreamer 가설이 Fact-Checker를 통과 — 노란 채움 + 초록 테두리."""
    return source_type == "inferred" and check_status == "promoted"
