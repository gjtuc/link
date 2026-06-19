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

echo [1/2] 문서 추출 패키지 확인...
pip install pypdf python-docx -q

echo [2/2] 웹 UI 시작 (http://127.0.0.1:8765)
start "" "http://127.0.0.1:8765/"
python -m deconstructor.web.server
pause
