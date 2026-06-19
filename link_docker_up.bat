@echo off
REM Neo4j를 Docker로 기동 (link 프로젝트용)
REM 비밀번호: deconstructor-dev  (docker-compose.yml 과 동일)
chcp 65001 >nul
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
    echo [오류] Docker가 설치되어 있지 않습니다.
    echo        link_docker_install.bat 안내를 먼저 따르세요.
    pause
    exit /b 1
)

echo.
echo  [주의] Neo4j Desktop 이 켜져 있으면 포트 7687 충돌합니다.
echo         Desktop의 link 인스턴스를 Stop 한 뒤 진행하세요.
echo.
pause

docker compose up -d
if errorlevel 1 (
    echo [오류] docker compose up 실패
    pause
    exit /b 1
)

echo.
echo  Neo4j Docker 기동 완료
echo    Browser : http://localhost:7474
echo    Bolt    : bolt://localhost:7687
echo    User    : neo4j
echo    Password: deconstructor-dev
echo.
echo  local_settings.py 에 아래를 넣으세요:
echo    NEO4J_URI = "bolt://localhost:7687"
echo    NEO4J_PASSWORD = "deconstructor-dev"
echo.
pause
