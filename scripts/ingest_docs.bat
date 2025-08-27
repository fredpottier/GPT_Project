@echo off
setlocal
cd /d "%~dp0\.."
echo Ingesting docs from data\docs into Qdrant...
curl -X POST http://localhost:%APP_PORT%/ingest -H "x-api-key: %APP_API_KEY%"
echo.
endlocal
