@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\.."

if not exist ".env" (
  echo [ERREUR] .env introuvable dans le dossier racine du projet.
  echo Copiez .env.example en .env puis remplissez vos valeurs.
  pause
  exit /b 1
)

REM Optionnel: charger quelques vars pour affichage
for /f "usebackq tokens=1,2 delims==" %%A in (`powershell -NoProfile -Command ^
  "(Get-Content .env | Where-Object {$_ -match '^(APP_PORT|APP_UI_PORT)='})"`) do (
  set "%%A=%%B"
)

echo Building app image...
docker compose build app
if errorlevel 1 (
  echo [ERREUR] Echec build 'app'.
  pause
  exit /b 1
)

echo Starting stack...
docker compose up -d
if errorlevel 1 (
  echo [ERREUR] Echec docker compose up.
  pause
  exit /b 1
)

echo.
echo App API:   http://localhost:%APP_PORT%
echo UI:        http://localhost:%APP_UI_PORT%
echo Zep:       http://localhost:8000
echo Qdrant:    http://localhost:6333
echo.
endlocal
