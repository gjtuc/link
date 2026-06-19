"""LangGraph node wrapper for The Weaver.

=======================================



## 목적 / Purpose



파이프라인 최종 State에서 검증된 엣지·엔드포인트 facts를 추출해 적절한 Store

(`ConsoleWeaver` / `Neo4jWeaver`)에 `persist` 호출한다. 결과는 `weaver_result`에 기록.



Extracts verified edges and endpoint facts from final State and calls `persist` on the

appropriate store (`ConsoleWeaver` / `Neo4jWeaver`). Result stored in `weaver_result`.



## 파이프라인 위치 / Pipeline Position



::



    skeptic → weaver_node(persist_db=...) → END



`graph/builder.py`에서 `partial(weaver_node, persist_db=persist_db)`로 바인딩.



Bound via `partial(weaver_node, persist_db=persist_db)` in `graph/builder.py`.



## 수정 가이드 / Modification Guide



- Store 선택 로직만 여기 유지; Cypher/로깅은 각 store 클래스.

- Neo4j 연결은 `try/finally`로 `close()` — 리소스 누수 방지.

- 새 backend(예: SQLite) 추가 시 동일 `persist(...)` 시그니처의 클래스 + 분기.

- `TYPE_CHECKING`으로 State 순환 import 방지 패턴 유지.

"""



from __future__ import annotations



from typing import TYPE_CHECKING



from deconstructor.weaver.console_store import ConsoleWeaver

from deconstructor.weaver.neo4j_store import Neo4jWeaver

from deconstructor.weaver.resolve import facts_for_verified_edges



if TYPE_CHECKING:

    from deconstructor.pipeline.state import State





def weaver_node(state: "State", *, persist_db: bool) -> dict:

    """

    Persist verified causal edges and their endpoint facts only.



    Default (``persist_db=False``): console weaver, no Neo4j connection.



    검증된 인과 엣지와 엔드포인트 facts만 영속화. 기본은 콘솔 모드.

    """

    edges = state["verified_edges"]

    # W10: completed_facts 중 엣지 끝점·원자 fact만 선별

    facts = facts_for_verified_edges(state["completed_facts"], edges)

    partial_run = state.get("partial_run", False)



    if persist_db:

        store = Neo4jWeaver()

        try:

            result = store.persist(

                trigger_event=state["raw_text"],

                facts=facts,

                edges=edges,

                partial_run=partial_run,

            )

        finally:

            # 드라이버 세션 종료 — CLI 1회 실행 후에도 연결 정리

            store.close()

    else:

        # --no-db 기본: Neo4j 없이 WeaverResult 메타만 생성

        result = ConsoleWeaver().persist(

            trigger_event=state["raw_text"],

            facts=facts,

            edges=edges,

            partial_run=partial_run,

        )



    return {"weaver_result": result}

