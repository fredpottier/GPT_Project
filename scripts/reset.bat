@echo off
setlocal
cd /d "%~dp0\.."
echo WARNING: This will delete volumes (Zep, Postgres, Qdrant, checkpoints, logs)!
pause
docker compose down -v
rmdir /S /Q data\postgres
rmdir /S /Q data\zep
rmdir /S /Q data\qdrant
rmdir /S /Q data\checkpoints
rmdir /S /Q data\logs
mkdir data\postgres
mkdir data\zep
mkdir data\qdrant
mkdir data\checkpoints
mkdir data\logs
mkdir data\docs
echo Reset done. Run scripts\start.bat to restart fresh.
endlocal
