@echo off
REM Link UI — 서버가 없으면 백그라운드 기동 후 브라우저만 연다 (이 창은 바로 닫혀도 됨)
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765/api/status' -TimeoutSec 2).StatusCode } catch { 0 }" 2>nul | findstr /x "200" >nul
if errorlevel 1 (
    echo [LinkUI] 서버 시작 중 ^(백그라운드^)...
    start /min "" cmd /c ""%~dp0link_ui_serve.bat""
    timeout /t 3 /nobreak >nul
)

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
    start "" "http://127.0.0.1:8765/"
)
