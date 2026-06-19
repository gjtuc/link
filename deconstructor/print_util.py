"""Windows cp949 터미널 안전 출력 (cli 패키지와 분리 — 순환 import 방지)."""

from __future__ import annotations

import sys


def safe_print(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(encoding, errors="replace").decode(encoding))
