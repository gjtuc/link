"""Neo4j weaver — ``--db`` 플래그 시 선택적 영속화

=================================================



## 목적 / Purpose



검증된 `CausalEdge`와 엔드포인트 `Fact` 노드를 Neo4j에 MERGE한다.

`Fact.id` 유니크 제약과 `CAUSES` 관계(probability, latency)를 기록한다.



MERGEs verified `CausalEdge` and endpoint `Fact` nodes into Neo4j.

Creates `Fact.id` uniqueness constraint and `CAUSES` relationships (probability, latency).



## 파이프라인 위치 / Pipeline Position



::



    weaver_node(persist_db=True) → Neo4jWeaver.persist → WeaverResult



`config.NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 필요. 엣지 없으면 skip_reason 반환.



Requires `config.NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`. Returns skip_reason when no edges.



## 수정 가이드 / Modification Guide



- Cypher 변경 시 `_ensure_schema` 제약과 MERGE 키(`id`) 일치 유지.

- `trigger_event`는 노드 속성으로 보존 — 감사·재현용.

- `db/neo4j_client.py`가 이 클래스를 re-export — public API 이름 변경 시 동기화.

- 통합 테스트: Neo4j testcontainer 또는 mock driver 권장.

"""



from __future__ import annotations



from neo4j import Driver, GraphDatabase



from deconstructor import config

from deconstructor.models import AtomicFact, CausalEdge

from deconstructor.weaver.schemas import WeaverResult





class Neo4jWeaver:

    """Persist only verified-edge endpoint facts and CAUSES relationships."""



    def __init__(self) -> None:

        # config에서 URI·인증 로드 — local_settings / .env

        self._driver: Driver = GraphDatabase.driver(

            config.NEO4J_URI,

            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),

        )



    def close(self) -> None:

        self._driver.close()



    def _ensure_schema(self) -> None:

        """Fact.id 유니크 제약 — MERGE 충돌 방지."""

        with self._driver.session() as session:

            session.run(

                """

                CREATE CONSTRAINT fact_id IF NOT EXISTS

                FOR (f:Fact) REQUIRE f.id IS UNIQUE

                """

            )



    def persist(

        self,

        *,

        trigger_event: str,

        facts: list[AtomicFact],

        edges: list[CausalEdge],

        partial_run: bool = False,

    ) -> WeaverResult:

        # 엣지 없음 → DB 터치 없이 skipped WeaverResult

        if not edges:

            return WeaverResult(

                mode="neo4j",

                skipped_reason="no verified edges to persist",

                partial_run=partial_run,

            )



        self._ensure_schema()



        with self._driver.session() as session:

            # 엔드포인트 Fact 노드 MERGE + 속성 SET

            for fact in facts:

                session.run(

                    """

                    MERGE (f:Fact {id: $id})

                    SET f.subject = $subject,

                        f.state_change = $state_change,

                        f.is_atomic = true,

                        f.timestamp = $timestamp,

                        f.trigger_event = $trigger_event

                    """,

                    id=fact.id,

                    subject=fact.subject,

                    state_change=fact.state_change,

                    timestamp=fact.timestamp.isoformat() if fact.timestamp else None,

                    trigger_event=trigger_event,

                )



            # 검증된 인과 관계 CAUSES MERGE

            for edge in edges:

                session.run(

                    """

                    MATCH (src:Fact {id: $source_id})

                    MATCH (tgt:Fact {id: $target_id})

                    MERGE (src)-[r:CAUSES]->(tgt)

                    SET r.probability = $probability,

                        r.latency = $latency

                    """,

                    source_id=edge.source_fact_id,

                    target_id=edge.target_fact_id,

                    probability=edge.probability,

                    latency=edge.latency,

                )



        pairs = [(e.source_fact_id, e.target_fact_id) for e in edges]

        return WeaverResult(

            mode="neo4j",

            nodes_written=len(facts),

            edges_written=len(edges),

            fact_ids=[f.id for f in facts],

            edge_pairs=pairs,

            partial_run=partial_run,

        )

