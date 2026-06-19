# -*- coding: utf-8 -*-
"""Neo4j :Fact / :CAUSES 전체 삭제 — 테스트·세션 초기화."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from deconstructor import config
from neo4j import GraphDatabase


def clear_graph() -> tuple[int, int]:
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    with driver.session() as s:
        before_f = s.run("MATCH (f:Fact) RETURN count(f) AS c").single()["c"]
        before_e = s.run("MATCH ()-[r:CAUSES]->() RETURN count(r) AS c").single()["c"]
        s.run("MATCH ()-[r:CAUSES]->() DELETE r")
        s.run("MATCH (f:Fact) DELETE f")
    driver.close()
    return before_f, before_e


if __name__ == "__main__":
    n, e = clear_graph()
    print(f"[OK] Neo4j 초기화 — Fact {n}개, CAUSES {e}개 삭제")
