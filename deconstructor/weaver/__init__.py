"""The Weaver — 검증된 인과 그래프 영속화 (console 또는 Neo4j)

================================================================



## 목적 / Purpose



skeptic가 확정한 `verified_edges`와 그 끝점 facts를 **콘솔 로그** 또는 **Neo4j MERGE**로

저장한다. 기본은 DB 없이 `ConsoleWeaver`; `--db` 시 `Neo4jWeaver`.



Persists skeptic-confirmed `verified_edges` and endpoint facts via **console log** or

**Neo4j MERGE**. Default: `ConsoleWeaver` without DB; `--db` enables `Neo4jWeaver`.



## 파이프라인 위치 / Pipeline Position



::



    skeptic → weaver_node → END

                ↓

         WeaverResult in State



파이프라인 **종단 노드**. `partial_run` 플래그는 depth cap 등 부분 실행 시 메타데이터로 전달.



**Terminal pipeline node**. `partial_run` propagates metadata for partial runs (e.g. depth cap).



## 수정 가이드 / Modification Guide



- 영속 대상 facts 필터 → `resolve.facts_for_verified_edges`.

- 스키마·결과 DTO → `schemas.WeaverResult`.

- Neo4j Cypher·제약 → `neo4j_store.py`; config는 `deconstructor.config`.

- LangGraph 바인딩 → `weaver/node.py`, `graph/builder.py`의 `persist_db` partial.

"""



from deconstructor.weaver.resolve import facts_for_verified_edges

from deconstructor.weaver.schemas import WeaverResult



__all__ = ["WeaverResult", "facts_for_verified_edges"]

