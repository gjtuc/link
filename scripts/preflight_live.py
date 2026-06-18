#!/usr/bin/env python3
"""
라이브 실행 전 환경 점검 스크립트
==================================

사용법:
  python scripts/preflight_live.py

확인 항목:
  1. GEMINI_API_KEY 또는 OPENAI_API_KEY (config.resolve_llm_provider)
  2. LangChain chat model 인스턴스 생성
  3. Neo4j bolt 연결 (NEO4J_PASSWORD)

실패 시 local_settings.py 복사·키 설정 안내.
Neo4j 없어도 LLM만 OK면 exit 0 + WARN (--db 없이 실행 가능).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from deconstructor import config


def main() -> int:
    ok = True
    provider = config.resolve_llm_provider()
    print("== deconstructor live preflight ==")
    print(f"LLM provider : {provider or '(none)'}")
    # 키 값 자체는 출력하지 않음 (보안)
    print(f"GEMINI_API_KEY: {'set' if config.GEMINI_API_KEY else 'missing'}")
    print(f"OPENAI_API_KEY: {'set' if config.OPENAI_API_KEY else 'missing'}")
    print(f"GEMINI_MODEL  : {config.GEMINI_MODEL}")
    print(f"NEO4J_URI     : {config.NEO4J_URI}")
    print(f"NEO4J_PASSWORD: {'set' if config.NEO4J_PASSWORD else 'missing'}")

    if not provider:
        print("\n[FAIL] No LLM key. Copy deconstructor/local_settings.example.py")
        print("       -> deconstructor/local_settings.py and set GEMINI_API_KEY.")
        ok = False
    else:
        try:
            from deconstructor.llm import get_chat_model

            model = get_chat_model()
            print(f"\n[OK] LLM client: {type(model).__name__}")
        except Exception as exc:
            print(f"\n[FAIL] LLM client: {exc}")
            ok = False

    if not config.NEO4J_PASSWORD:
        print("\n[WARN] NEO4J_PASSWORD missing - use --db only after Neo4j is up.")
        ok_db = False
    else:
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
            )
            driver.verify_connectivity()
            driver.close()
            print("[OK] Neo4j connectivity")
            ok_db = True
        except Exception as exc:
            print(f"[FAIL] Neo4j: {exc}")
            print("       Start Neo4j Desktop or docker compose, then retry.")
            ok_db = False

    if not ok:
        return 1
    if not ok_db:
        print("\n[INFO] LLM ready; Neo4j not ready - run without --db first.")
    else:
        print("\n[OK] Ready for: python main.py \"headline\" --db")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
