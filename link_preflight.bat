@echo off
REM link_preflight.bat — LLM·Neo4j 연결 점검
chcp 65001 >nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
python scripts\preflight_live.py
pause
