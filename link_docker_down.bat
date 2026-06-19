@echo off
chcp 65001 >nul
cd /d "%~dp0"
docker compose down
echo Neo4j Docker 중지됨.
pause
