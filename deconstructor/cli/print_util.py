"""
print_util — Windows cp949 터미널 안전 출력
============================================

## 목적 / Purpose

stdout 인코딩이 UTF-8이 아닌 Windows 콘솔(cp949 등)에서 **UnicodeEncodeError** 없이
텍스트를 출력한다. 실패 시 replace 폴백으로 깨진 문자 대신 ``?`` 등으로 대체.

Prints text without **UnicodeEncodeError** on Windows consoles (cp949, etc.) where
stdout encoding is not UTF-8. On failure, uses replace fallback for unmappable chars.

## 파이프라인 위치 / Pipeline Position

::

    run_dry_traced / run_live → safe_print(format_*_report(...))

사람이 읽는 리포트 출력 전용; `--json` 경로는 일반 `print`도 사용됨.

For human-readable reports; `--json` paths may use plain `print` as well.

## 수정 가이드 / Modification Guide

- 리포트 문자열에 이모지·특수기호 추가 시 이 유틸 경유 권장.
- stderr 분리 필요 시 동일 패턴으로 `safe_print_stderr` 추가 가능.
"""

from __future__ import annotations

import sys


def safe_print(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        # cp949 등에서 인코딩 불가 문자 → replace 후 출력
        print(text.encode(encoding, errors="replace").decode(encoding))
