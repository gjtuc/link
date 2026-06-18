"""Report footer — success banner and weaver mode echo.
리포트 푸터 — 성공 배너 및 위버 mode 반복.

Purpose / 목적
--------------
Closes the report with ``SEP`` banners and a one-line OK message. Uses
``DRY-RUN OK`` when weaver ran in console mode (typical dry-run), else
``PIPELINE OK``.
``SEP`` 배너와 OK 한 줄로 마무리. weaver가 console mode면 ``DRY-RUN OK``,
아니면 ``PIPELINE OK``.

Pipeline position / 파이프라인 위치
-----------------------------------
Last block in ``compose.format_dry_run_report``.
``compose.format_dry_run_report`` **마지막 블록**.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Footer text is used in CLI exit messaging — keep strings stable or update tests.
- ``weaver is None`` → mode ``n/a``, footer ``PIPELINE OK``.
- CLI 종료 메시지에 사용 — 문자열 변경 시 테스트 갱신.
"""

from __future__ import annotations

from deconstructor.pipeline.state import State
from deconstructor.report.sections._constants import SEP


def format_footer_section(state: State) -> list[str]:
    """Return closing banner lines (no leading blank line)."""
    weaver = state.get("weaver_result")
    # console mode => dry-run path without DB persistence.
    # console mode => DB 없는 dry-run 경로.
    footer = "DRY-RUN OK" if weaver and weaver.mode == "console" else "PIPELINE OK"
    mode = weaver.mode if weaver else "n/a"
    return [SEP, f"  {footer} - weaver mode={mode}", SEP]
