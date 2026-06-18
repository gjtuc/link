"""Console-only weaver — 기본 ``--no-db`` 동작
=============================================

## 목적 / Purpose

Neo4j에 연결하지 않고 **영속화 의도**를 `WeaverResult` 메타데이터로만 기록한다.
노드/엣지 개수·ID 쌍을 반환해 CLI 리포트·JSON 출력이 동일 스키마를 사용하게 한다.

Records persistence **intent** as `WeaverResult` metadata without touching Neo4j.
Returns node/edge counts and ID pairs so CLI report/JSON use the same schema.

## 파이프라인 위치 / Pipeline Position

::

    weaver_node(persist_db=False) → ConsoleWeaver.persist → WeaverResult(mode="console")

dry-run·live 공통 기본 경로. `--db` 없으면 항상 이 구현.

Default path for dry-run and live when `--db` is absent.

## 수정 가이드 / Modification Guide

- 실제 print/logging 추가 시 `cli/print_util` 인코딩 이슈(cp949) 고려.
- `Neo4jWeaver.persist`와 반환 필드·skip 조건 동기화 유지.
- skipped_reason 문구 변경 시 테스트 스냅샷 갱신.
"""

from __future__ import annotations

from deconstructor.models import AtomicFact, CausalEdge
from deconstructor.weaver.schemas import WeaverResult


class ConsoleWeaver:
    """Log persistence intent without touching Neo4j."""

    def persist(
        self,
        *,
        trigger_event: str,
        facts: list[AtomicFact],
        edges: list[CausalEdge],
        partial_run: bool = False,
    ) -> WeaverResult:
        if not edges:
            return WeaverResult(
                mode="console",
                skipped_reason="no verified edges to persist",
                partial_run=partial_run,
            )

        # Neo4j와 동일한 요약 필드 — mode만 "console"
        pairs = [(e.source_fact_id, e.target_fact_id) for e in edges]
        return WeaverResult(
            mode="console",
            nodes_written=len(facts),
            edges_written=len(edges),
            fact_ids=[f.id for f in facts],
            edge_pairs=pairs,
            partial_run=partial_run,
        )
