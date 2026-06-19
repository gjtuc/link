@echo off
REM link_run.bat — Deconstructor 라이브 실행 (Neo4j + 그래프)
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".env" (
    echo [오류] .env 없음 — .env.example 을 복사한 뒤 GEMINI_API_KEY, NEO4J_PASSWORD 를 채우세요.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if "%~1"=="" (
    set "HEADLINE=[단독] 10:00 grid power가 off됐다. 10:02 factory A power supply가 interrupted됐다."
) else (
    set "HEADLINE=%~1"
)

echo.
echo  Deconstructor 실행 — Neo4j 저장 + 그래프 오픈
echo  헤드라인: %HEADLINE%
echo.

python main.py "%HEADLINE%" --db
exit /b %ERRORLEVEL%
