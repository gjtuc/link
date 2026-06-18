"""
The Ultimate Deconstructor & Causal Graph Engine (v0.2.0)
============================================================

## 프로젝트 목표 (다른 AI·개발자용 요약)

뉴스·헤드라인 같은 **서술(narrative)** 을 기계적 **원자 사실(atomic facts)** 로 분해하고,
인과 규칙 엔진(The Skeptic)으로 **상관(correlation)을 거부**하고 **기계적 인과(causation)** 만
검증한 뒤, Neo4j 그래프 DB에 저장·시각화하는 LangGraph 파이프라인이다.

핵심 철학:
  - 감정·평가·전망 토큰은 스키마에 없음 → LLM 출력은 Pydantic으로 강제
  - 인과 판정은 LLM 내러티브가 아니라 **코드화된 규칙(R01~R11)** 으로만 수행
  - Weaver는 **검증된 엣지의 양 끝 노드만** DB에 기록 (과잉 저장 방지)

## 디렉터리 맵 (수정 시 어디를 볼지)

  main.py              → CLI 진입점 (실제 로직은 deconstructor/cli/)
  deconstructor/
    config.py          → .env + local_settings.py 로드, Neo4j/LLM 키
    models.py          → AtomicFact, FactList, CausalEdge 스키마 (변경 시 전 파이프라인 영향)
    graph/builder.py   → LangGraph 컴파일·실행 (노드 추가/순서 변경은 여기)
    pipeline/state.py  → LangGraph 공유 State TypedDict
    deconstruct/       → LLM으로 비원자 사실 분해
    verify/            → is_atomic 분리 (completed vs extracted)
    routing/           → verify 후 deconstruct 루프 vs skeptic 분기
    skeptic/           → 인과 규칙 엔진 + INCONCLUSIVE 재시도
    weaver/            → 콘솔 또는 Neo4j 영속화 (--db)
    viz/               → 파이프라인 종료 후 pyvis HTML + 브라우저 자동 오픈
    cli/               → argparse, live/dry-run 모드 분기
    report/            → 터미널 리포트 포맷터
    llm/               → Gemini / OpenAI LangChain 래퍼

## 파이프라인 흐름 (LangGraph)

  deconstruct → verify → [루프: non-atomic & depth<cap → deconstruct]
                      → skeptic → weaver → END

  --dry-run  : stub deconstruct (LLM 없음), skeptic mechanism도 stub
  --db       : Neo4jWeaver + 종료 후 viz.export.maybe_visualize_after_pipeline()

## 공개 API (이 패키지에서 re-export)

  AtomicFact, CausalEdge, FactList — 외부·테스트에서 가장 많이 import하는 타입.
"""

from deconstructor.models import AtomicFact, CausalEdge, FactList

__all__ = ["AtomicFact", "CausalEdge", "FactList"]
__version__ = "0.2.0"
