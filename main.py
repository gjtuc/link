"""
Deconstructor CLI 진입점
========================

실행 예:
  python main.py "헤드라인 텍스트" --db     # 라이브 LLM + Neo4j + 브라우저 그래프
  python main.py --dry-run                  # stub LLM, 콘솔 weaver
  python main.py --dry-run --db             # stub + Neo4j + viz

모든 인자 파싱·모드 분기는 `deconstructor.cli.dispatch` 에 위임.
이 파일은 얇은 래퍼만 유지 — 로직 추가 시 cli/ 쪽을 수정할 것.
"""

from __future__ import annotations

from deconstructor.cli.dispatch import dispatch


def main(argv: list[str] | None = None) -> int:
    """CLI 메인. argv 미지정 시 sys.argv 사용. 종료 코드 0=성공."""
    return dispatch(argv)


if __name__ == "__main__":
    raise SystemExit(main())
