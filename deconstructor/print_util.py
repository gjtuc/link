"""Windows cp949 터미널 안전 출력 (cli 패키지와 분리 — 순환 import 방지)."""

from __future__ import annotations

import io
import sys


def bootstrap_stdio_utf8() -> None:
    """Windows cp949 콘솔 등에서 stdout/stderr를 UTF-8로 재설정."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass


def safe_print(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    if encoding.lower().replace("_", "-") in ("cp949", "euc-kr", "ascii"):
        text = text.encode(encoding, errors="replace").decode(encoding)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(encoding, errors="replace").decode(encoding))


def safe_write(stream: io.TextIOBase, text: str) -> None:
    """print 없이 스트림에 UTF-8 안전 기록."""
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        stream.write(text)
        stream.flush()
    except UnicodeEncodeError:
        stream.write(text.encode(encoding, errors="replace").decode(encoding))
        stream.flush()
