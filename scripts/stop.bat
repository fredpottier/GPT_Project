@echo off
setlocal
cd /d "%~dp0\.."
echo Stopping stack...
docker compose down
endlocal