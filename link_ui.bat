@echo off
REM link_ui.bat — Google 번역 스타일 웹 UI (텍스트/이미지/문서 → 그래프)
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [오류] venv 없음 — link_start.bat 으로 먼저 설치하세요.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/2] 패키지 확인 (문서 추출 + SSL 프록시)...
pip install pypdf python-docx pip-system-certs -q

echo [2/2] 웹 UI 시작 (http://127.0.0.1:8765)
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)
if defined CHROME_EXE (
    start "" "%CHROME_EXE%" "http://127.0.0.1:8765/"
) else (
    echo [경고] Chrome을 찾지 못함 — 기본 브라우저로 엽니다.
    start "" "http://127.0.0.1:8765/"
)
python -m deconstructor.web.server
pause
