"""
db 패키지 — Neo4j 영속화 하위 호환 re-export
=============================================

## 목적 / Purpose

구버전 코드가 `deconstructor.db.Neo4jGraphStore`로 import하던 경로를 유지한다.
실제 구현은 `weaver.neo4j_store.Neo4jWeaver`에 있다.

Preserves legacy imports of `deconstructor.db.Neo4jGraphStore`.
Implementation lives in `weaver.neo4j_store.Neo4jWeaver`.

## 파이프라인 위치 / Pipeline Position

::

    external / legacy scripts → db.Neo4jGraphStore
    current pipeline          → weaver.Neo4jWeaver (preferred)

## 수정 가이드 / Modification Guide

- **로직 변경은 weaver/neo4j_store.py** — 이 패키지는 alias만.
- `WeaverOutput` = `WeaverResult` alias — 이름 변경 시 deprecation 주기 고려.
"""

from deconstructor.db.neo4j_client import Neo4jGraphStore

__all__ = ["Neo4jGraphStore"]
