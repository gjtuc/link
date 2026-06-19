@echo off
REM Link UI 서버만 백그라운드 실행 (창 최소화·로그 파일). link_ui.bat / 자동 시작용.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [LinkUI] venv 없음 — link_start.bat 으로 한 번 설치하세요. >> "%~dp0logs\link_ui.log"
    exit /b 1
)

if not exist "logs" mkdir "logs"

REM 이미 떠 있으면 종료
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765/api/status' -TimeoutSec 2).StatusCode } catch { 0 }" 2>nul | findstr /x "200" >nul
if not errorlevel 1 exit /b 0

call venv\Scripts\activate.bat
pip install pypdf python-docx pip-system-certs -q >> "logs\link_ui.log" 2>&1

echo [%date% %time%] Link UI server starting >> "logs\link_ui.log"
python -m deconstructor.web.server >> "logs\link_ui.log" 2>&1
