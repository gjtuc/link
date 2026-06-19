@echo off
REM Docker Desktop 설치 안내 (Windows 10)
chcp 65001 >nul
echo.
echo ============================================================
echo   Docker 설치 — link 프로젝트 (Neo4j 컨테이너)
echo ============================================================
echo.
echo  이 PC: Windows 10 Pro, 빌드 18363
echo.
echo  Docker Desktop 은 보통 Windows 10 빌드 19041 이상 + WSL2 가 필요합니다.
echo  지금 PC가 더 낮으면 Windows Update 로 OS를 먼저 올리는 것을 권장합니다.
echo.
echo  --- 설치 순서 (한 번만) ---
echo.
echo  1. Windows Update
echo     설정 -^> 업데이트 및 보안 -^> Windows Update -^> 업데이트 확인
echo     (목표: 빌드 19041 이상, 가능하면 22H2)
echo.
echo  2. WSL2 (PowerShell 관리자)
echo     wsl --install
echo     재부팅
echo.
echo  3. Docker Desktop
echo     https://www.docker.com/products/docker-desktop/
echo     설치 후 Docker Desktop 실행 -^> Settings -^> WSL2 사용 확인
echo.
echo  4. 확인 (새 cmd)
echo     docker --version
echo     docker compose version
echo.
echo  --- link 에서 Neo4j 쓰기 ---
echo.
echo  Neo4j Desktop 과 Docker Neo4j 는 동시에 쓸 수 없습니다 (포트 7687).
echo  둘 중 하나만 선택:
echo    A) Neo4j Desktop (지금 켜 둔 link) — 설정만 하면 됨
echo    B) Docker — link_docker_up.bat
echo.
echo  Docker 사용 시 local_settings.py:
echo    NEO4J_PASSWORD = "deconstructor-dev"
echo.
echo ============================================================
echo.
pause
start https://www.docker.com/products/docker-desktop/
start https://learn.microsoft.com/ko-kr/windows/wsl/install
