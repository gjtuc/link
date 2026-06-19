"""
Deconstructor CLI 진입점
========================

실행 예:
  python main.py "헤드라인" --db     # 파이프라인 + Neo4j + Step 4 브라우저 viz
  python main.py --dry-run --db

Step 4 결합:
  dispatch() 로 파이프라인 실행 후, exit 0 이고 --db 이면
  maybe_visualize_after_pipeline() 호출 (main 마지막).
"""

from __future__ import annotations

from deconstructor.cli.dispatch import dispatch
from deconstructor.cli.parser import build_parser
from deconstructor.viz.export import maybe_visualize_after_pipeline


def main(argv: list[str] | None = None) -> int:
    """CLI 메인. 파이프라인 성공 + --db 시 Step 4 시각화."""
    args = build_parser().parse_args(argv)
    exit_code = dispatch(argv)

    # Step 4: 파이프라인 완료 직후 end-to-end viz (--db, skeptic-only 제외)
    if exit_code == 0 and args.db and not args.skeptic_only:
        maybe_visualize_after_pipeline(persist_db=True)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
