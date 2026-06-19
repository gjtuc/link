"""
로컬 비밀 설정 템플릿 — 이 파일을 복사해 local_settings.py 로 저장
================================================================

  cp deconstructor/local_settings.example.py deconstructor/local_settings.py

그 다음 GEMINI_API_KEY, NEO4J_PASSWORD 등을 채운 뒤 **저장(Ctrl+S)**.
config.py 가 import 시점에 local_settings 를 덮어씀.

주의:
  - local_settings.py 는 .gitignore — 절대 커밋하지 말 것
  - gemini-2.0-flash / gemini-2.5-flash 는 일부 계정 404 → 3.x 권장
  - 에디터에만 있고 디스크에 저장 안 된 변경은 Python이 못 봄
"""

# --- LLM (Gemini — 권장, 상황별 이원화) ---
GEMINI_API_KEY = ""
# 빠른 작업: 이미지 OCR, 가벼운 추출
GEMINI_MODEL_FLASH = "gemini-3.5-flash"
GEMINI_THINKING_LEVEL_FLASH = "medium"
# 깊은 추론: Deconstruct, URL/PDF 요약, Dreamer, Fact-Checker
GEMINI_MODEL_PRO = "gemini-3.1-pro-preview"
GEMINI_THINKING_LEVEL_PRO = "high"

# --- LLM (OpenAI — 대안) ---
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"

# auto | gemini | openai
LLM_PROVIDER = "gemini"

# --- Tavily (Fact-Checker --enable-dreamer live search) ---
TAVILY_API_KEY = ""

# --- Neo4j (main.py --db, viz 자동 오픈) ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = ""
