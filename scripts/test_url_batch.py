# -*- coding: utf-8 -*-
"""일회성 URL 배치 테스트."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from deconstructor.viz.export import maybe_visualize_after_pipeline
from deconstructor.web.extract import extract_batch

URLS = [
    "https://www.hankyung.com/article/2026061967317",
    "https://www.yonhapnewstv.co.kr/news/MYH20260619163653ZAn",
    "https://www.yonhapnewstv.co.kr/news/MYH20260619170121GTR",
    "https://www.yna.co.kr/amp/view/AKR20260619027800504",
]


def main() -> int:
    from deconstructor.cli.modes.live import run_live

    print("=== URL 추출 ===")
    sources = extract_batch(urls=URLS)
    for i, s in enumerate(sources, 1):
        print(f"[{i}] {s.label}")
        print(f"    {s.text[:180]}...\n")

    print("=== 파이프라인 (건당 Neo4j 저장) ===")
    for i, s in enumerate(sources, 1):
        print(f"\n--- {i}/{len(sources)}: {s.label} ---")
        code = run_live(s.text, persist_db=True, as_json=False)
        if code != 0:
            print(f"[FAIL] exit {code}")
            return code

    print("\n=== 그래프 생성 ===")
    maybe_visualize_after_pipeline(persist_db=True)
    print("\n[OK] graph_output.html 갱신 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
