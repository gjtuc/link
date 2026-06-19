# -*- coding: utf-8 -*-
"""Neo4j Fact 목록 조회."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from deconstructor import config
from neo4j import GraphDatabase

driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
with driver.session() as s:
    total = s.run("MATCH (f:Fact) RETURN count(f) AS c").single()["c"]
    edges = s.run("MATCH ()-[r:CAUSES]->() RETURN count(r) AS c").single()["c"]
    print(f"Facts: {total}, CAUSES: {edges}\n")

    print("=== factory/grid (테스트 잔재) ===")
    for r in s.run(
        """
        MATCH (f:Fact)
        WHERE toLower(f.subject) CONTAINS 'factory'
           OR toLower(f.subject) CONTAINS 'grid'
           OR f.subject CONTAINS '단전'
        RETURN DISTINCT f.subject AS subject ORDER BY subject
        """
    ).data():
        print(" ", r["subject"])

    print("\n=== 참가자 / DAPA (4번 기사) ===")
    for r in s.run(
        """
        MATCH (f:Fact)
        WHERE f.subject CONTAINS '참가' OR f.subject CONTAINS 'DAPA' OR f.subject CONTAINS '방위'
        RETURN DISTINCT f.subject AS subject ORDER BY subject
        """
    ).data():
        print(" ", r["subject"])

    print("\n=== Trump/MOU (1~3번 기사) ===")
    for r in s.run(
        """
        MATCH (f:Fact)
        WHERE toLower(f.subject) CONTAINS 'trump' OR f.subject CONTAINS 'MOU'
           OR f.subject CONTAINS '이재명' OR f.subject CONTAINS 'Lee'
        RETURN DISTINCT f.subject AS subject ORDER BY subject LIMIT 15
        """
    ).data():
        print(" ", r["subject"])

driver.close()
