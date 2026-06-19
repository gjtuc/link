@echo off
REM Neo4j 그래프 전체 초기화 (테스트 데이터 제거)
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo  [주의] Neo4j의 모든 Fact / CAUSES 가 삭제됩니다.
echo         (factory 테스트, 이전 기사 분석 결과 포함)
echo.
pause
python scripts\clear_neo4j.py
pause
