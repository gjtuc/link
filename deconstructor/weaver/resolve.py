"""Resolve which facts to persist alongside verified edges.

==========================================================



## 목적 / Purpose



weaver는 `completed_facts` 전체가 아니라 **검증된 엣지의 끝점(endpoint)이면서 원자인**

facts만 Neo4j/콘솔 결과에 포함한다. 불필요·거절된 가설 노드 유입을 방지한다.



The weaver includes only **atomic endpoint facts of verified edges**, not all

`completed_facts`. Prevents orphan or rejected-hypothesis nodes from being persisted.



## 파이프라인 위치 / Pipeline Position



::



    weaver_node → facts_for_verified_edges(completed_facts, verified_edges)



skeptic 출력 `verified_edges`와 verify 누적 `completed_facts`의 교집합 필터.



Intersection filter of skeptic output `verified_edges` and verify-accumulated

`completed_facts`.



## 수정 가이드 / Modification Guide



- W10-1/W10-2/W10-3 요구사항 주석 유지 — 정책 변경 시 skeptic/weaver 테스트.

- 엣지 방향(source→target)과 fact ID 일치는 `models.CausalEdge` 계약.

- 엔드포인트 외 컨텍스트 fact 저장 필요 시 스키마·Cypher 확장 검토.

"""



from __future__ import annotations



from deconstructor.models import AtomicFact, CausalEdge





def endpoint_fact_ids(edges: list[CausalEdge]) -> set[str]:

    """Collect all fact IDs referenced by verified causal edges."""

    ids: set[str] = set()

    for edge in edges:

        ids.add(edge.source_fact_id)

        ids.add(edge.target_fact_id)

    return ids





def facts_for_verified_edges(

    completed_facts: list[AtomicFact],

    verified_edges: list[CausalEdge],

) -> list[AtomicFact]:

    """

    W10-1: Only endpoint facts of verified edges.



    W10-2: Only atomic crumbs from completed_facts.

    W10-3: No rejected-hypothesis endpoints unless also in an edge.



    검증 엣지 끝점이면서 completed_facts에 있는 원자 fact만 반환.

    """

    if not verified_edges:

        return []



    needed = endpoint_fact_ids(verified_edges)

    return [

        f

        for f in completed_facts

        if f.id in needed and f.is_atomic

    ]

