@echo off

REM Link UI — Python 런처 (단계 L* 로그). Windows start \\ 버그 회피.

chcp 65001 >nul

set PYTHONIOENCODING=utf-8

cd /d "%~dp0"



set "PY=%~dp0venv\Scripts\python.exe"

if not exist "%PY%" (

    echo [LinkLaunch:L1-VENV] ERROR venv 없음 — link_start.bat 실행

    exit /b 1

)



"%PY%" "%~dp0link_launch.py"

exit /b %ERRORLEVEL%

