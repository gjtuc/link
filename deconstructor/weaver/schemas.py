"""Pydantic schemas for The Weaver persistence layer.

====================================================



## 목적 / Purpose



weaver pass(콘솔·Neo4j)의 **구조화된 결과 DTO**를 정의한다. LangGraph State의

`weaver_result` 필드 타입으로 사용되며 CLI JSON 직렬화에도 참여한다.



Defines the **structured result DTO** for a weaver pass (console/Neo4j). Used as the

`weaver_result` field type in LangGraph State and CLI JSON serialization.



## 파이프라인 위치 / Pipeline Position



::



    ConsoleWeaver / Neo4jWeaver → WeaverResult → State["weaver_result"]



파이프라인 종료 후 리포트·viz·외부 API의 단일 요약 객체.



Single summary object for reports, viz, and external APIs after pipeline completion.



## 수정 가이드 / Modification Guide



- 필드 추가 시 `pipeline/state.py` TypedDict·리포트 포맷터 동기화.

- `frozen=True` 유지 — 노드 간 불변 결과 스냅샷.

- `mode` Literal 확장 시 store 클래스·테스트 fixture 함께 수정.

"""



from __future__ import annotations



from typing import Literal



from pydantic import BaseModel, Field





class WeaverResult(BaseModel):

    """Result of a weaver pass (console or Neo4j)."""



    mode: Literal["console", "neo4j"] = "console"

    nodes_written: int = 0

    edges_written: int = 0

    fact_ids: list[str] = Field(default_factory=list)

    edge_pairs: list[tuple[str, str]] = Field(default_factory=list)

    skipped_reason: str = ""

    partial_run: bool = False



    model_config = {"frozen": True}

