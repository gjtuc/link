"""
neo4j_client — Neo4j 하위 호환 re-export 셔머
==============================================

## 목적 / Purpose

`Neo4jWeaver`를 `Neo4jGraphStore` 이름으로, `WeaverResult`를 `WeaverOutput`으로
re-export하여 레거시 import 경로를 지원한다.

Re-exports `Neo4jWeaver` as `Neo4jGraphStore` and `WeaverResult` as `WeaverOutput`
for legacy import paths.

## 파이프라인 위치 / Pipeline Position

::

    legacy: from deconstructor.db.neo4j_client import Neo4jGraphStore
    canonical: from deconstructor.weaver.neo4j_store import Neo4jWeaver

## 수정 가이드 / Modification Guide

- 신규 코드는 weaver 패키지 직접 import.
- alias 대상 클래스 rename 시 여기만 업데이트하면 legacy 호환 유지.
"""

from deconstructor.weaver.neo4j_store import Neo4jWeaver as Neo4jGraphStore
from deconstructor.weaver.schemas import WeaverResult as WeaverOutput

__all__ = ["Neo4jGraphStore", "WeaverOutput"]
