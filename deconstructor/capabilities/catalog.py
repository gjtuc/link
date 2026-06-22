"""
Q2/Q3 — 부하·미지원 catalog 시드 (JSON/코드, md 남발 금지).

μ-Q2-02 catalog portion — status untested|unsupported only.
스펙: docs/design/Q2-CAPABILITIES-spec.md § Q3 catalog 시드
"""

from __future__ import annotations

from typing import Any

CATALOG_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "id": "cat-pdf-triple",
        "status": "untested",
        "human_line": "PDF 세 개를 한꺼번에 올리는 건 아직 안 해봤어요. 한 번에 많이 넣으면 느려질 수 있어요.",
        "source": "catalog",
        "evidence": "probe 2026-06-22 exit 0 — 3 source_file, pipeline_ok, ~496s",
    },
    {
        "id": "cat-opju-origin",
        "status": "unsupported",
        "human_line": "Origin `.opju` 프로젝트 파일은 지금 Link가 읽지 못해요. PDF나 텍스트로보내 주세요.",
        "source": "catalog",
        "evidence": "extract 미구현 — 미지원 형식",
    },
    {
        "id": "cat-scanned-pdf",
        "status": "untested",
        "human_line": "스캔 PDF나 표만 있는 PDF는 글자 추출이 잘 안 될 수 있어요. 아직 충분히 검증하지 않았어요.",
        "source": "catalog",
        "evidence": "probe 2026-06-22 exit 2 — not_true_scan (no scan PDF); Phase-R ok",
    },
    {
        "id": "cat-file-10mb",
        "status": "untested",
        "human_line": "10MB 넘는 단일 파일은 메모리·시간이 많이 듭니다. 아직 큰 파일로는 안 해봤어요.",
        "source": "catalog",
        "evidence": "probe 미실행 — 크기 부하",
    },
    {
        "id": "cat-neo4j-off",
        "status": "untested",
        "human_line": "Neo4j가 꺼져 있어도 그래프는 보여 줄 수 있지만, 전체 동작은 Neo4j 켠 상태에서만 확인했어요.",
        "source": "catalog",
        "evidence": "probe 2026-06-22 exit 0 — bolt offline, pipeline_ok, ~292s (S5 auto-start skip 권장)",
    },
    {
        "id": "cat-gemini-429",
        "status": "untested",
        "human_line": "Gemini 일일 한도(429)에 걸리면 분석이 중간에 멈출 수 있어요. quota 리셋 후 다시 시도하세요.",
        "source": "catalog",
        "evidence": "probe 미실행 — 2026-06 Branch-1 quota 관측",
    },
)
