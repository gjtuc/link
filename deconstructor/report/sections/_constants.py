"""Shared visual constants for console report sections.
콘솔 리포트 섹션 공통 시각 상수.

Purpose / 목적
--------------
Single source for banner width and separator lines so header/footer stay
aligned across terminal widths and future section additions.
헤더·푸터 배너 폭과 구분선을 한곳에서 관리해 터미널 폭·신규 섹션과 정렬을 유지.

Pipeline position / 파이프라인 위치
-----------------------------------
Used only by ``header.py`` and ``footer.py`` — not part of data pipeline.
``header.py``, ``footer.py``에서만 사용 — 데이터 파이프라인 비참여.

Modification guide for other AIs / 다른 AI 수정 가이드
------------------------------------------------------
- Changing ``SEP`` length affects all report banners; update tests/snapshots if any.
- Import ``SEP`` here instead of duplicating ``"=" * N`` in section modules.
- ``SEP`` 길이 변경 시 배너 전체 폭 변경 — 스냅샷 테스트 있으면 함께 수정.
- 섹션 모듈에 ``"=" * N`` 복제 금지; 여기서 import.
"""

# Full-width equals banner (60 chars) — matches legacy CLI report layout.
# 60자 등호 배너 — 레거시 CLI 리포트 레이아웃과 동일.
SEP = "=" * 60
