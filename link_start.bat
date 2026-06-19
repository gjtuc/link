@echo off
REM link_start.bat — README 순서대로 Deconstructor 실행
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ============================================================
echo   Deconstructor (gjtuc/link) — 라이브 실행
echo   폴더: %CD%
echo ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [1/4] 가상환경 없음 — 생성 중...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo [1/4] venv OK
    call venv\Scripts\activate.bat
)

if not exist ".env" (
    echo [2/4] .env 없음 — .env.example 복사 후 키를 채우세요.
    copy .env.example .env
    notepad .env
    pause
    exit /b 1
)
echo [2/4] .env OK

echo [3/4] preflight...
python scripts\preflight_live.py
if errorlevel 1 (
    echo preflight 실패 — Gemini 키 / Neo4j Desktop 확인
    pause
    exit /b 1
)

echo.
echo [4/4] 파이프라인 실행 (Neo4j + graph_output.html)
if "%~1"=="" (
    python main.py "[단독] 10:00 grid power가 off됐다. 10:02 factory A power supply가 interrupted됐다." --db
) else (
    python main.py "%~1" --db
)

echo.
if exist "graph_output.html" echo 그래프: %CD%\graph_output.html
pause
