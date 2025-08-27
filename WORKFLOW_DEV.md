# 🚀 Workflow Quotidien pour GPT_Project

## 0) Démarrer l’environnement

### En Dev Container (recommandé)  
- **VS Code** : Dev Containers: Reopen in Container
- Cela lance db, qdrant, zep, ui et app.

### Ou en local  
- `docker compose up --build` 
- Code côté Windows avec volumes montés.

## 1) Modifier du code Python (fichiers sous `app/`)
- Éditez `app/*.py` → les changements sont immédiats (volumes bindés).
- Si l’app ne se reload pas toute seule : redémarrez juste le service app :
  - `docker compose restart app`
- → Pas besoin de rebuild pour du simple Python.

## 2) Gérer les dépendances Python

### A. En dev rapide
- Dans le terminal du container `app` :
  - `pip install packageX==1.2.3`
- Test. Puis figez dans le repo :
  - `pip freeze | grep -i packageX >> requirements.txt`

### B. Pour "figer proprement" dans l’image
- Ajustez `requirements.txt` puis :
  - `docker compose build app`
  - `docker compose up -d`
- Rebuild nécessaire pour CI/CD.

## 3) Changer une variable d'environnement
- Mettre dans `.env` (versionner plutôt un `.env.example`).
- Dans `docker-compose.yml`, référencez-les :
  ```yml
environment:
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  ```
- Appliquer :
  - `docker compose up -d`
  - Si problème : `docker compose up -d --force-recreate`

## 4) Modifier le Dockerfile
- Rebuild obligatoire :
  - `docker compose build app`
  - `docker compose up -d`

## 5) Schéma DB / Migrations / Données
- Si changement du schéma Postgres :
  - `docker compose down -v`  
  - `docker compose up -d --build`

## 6) Redémarrer / Arrêter proprement
- Restart rapide d’un service :
  - `docker compose restart app`
- Stop tout :
  - `docker compose down`
- Stop + clean volumes :
  - `docker compose down -v`

## 🧰 Raccourcis Utiles

### start.bat (Windows)
```bat
@echo off
cd /d "%~dp0"
docker compose up --build
pause
```

### stop.bat
```bat
@echo off
cd /d "%~dp0"
docker compose down
pause
```

### rebuild-app.bat
```bat
@echo off
cd /d "%~dp0"
docker compose build app
docker compose up -d
pause
```

## 🧪 Checklists Rapides

### Imports rouges (hors Dev Container)

#### Option propre :
- Créez un venv local iso au container :
  ```sh
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  docker compose exec app sh -lc "python -m pip freeze > /tmp/req.lock"
  docker cp gpt_project-app-1:/tmp/req.lock .\requirements.lock
  pip install -r requirements.lock
  ```
- **VS Code** : Python: Select Interpreter → `.venv`.

#### Option pragmatique :
- Masquer les warnings Pylance
  ```json
  {
    "python.analysis.disable": ["reportMissingImports","reportMissingModuleSource"],
    "python.analysis.diagnosticMode": "openFilesOnly"
  }
  ```

### Quand rebuild ?
- Code Python → non
- `requirements.txt` (figer dans l’image) → oui
- `Dockerfile` → oui
- Changement d’ENV dans l’image → oui (si seulement dans `docker-compose.yml` → non, juste `up -d`)

## 🧭 Git (Routine)
- `git status` # Voir les modifs
- `git add -p` # Ajouter par hunk
- `git commit -m "feat: clarification"`
- `git push`

### Branches :
- `git checkout -b feature/x`
  - ...dev...
  - `git add -p && git commit -m "feat: x"`
  - `git push -u origin feature/x` # Ouvre PR sur GitHub

## .gitignore Clé :
- `.venv/`
- `.env`
- `__pycache__/`
- `.vscode/`
- `data/`
- `*.log`
- `ui/node_modules/`

## TL;DR
- Éditez `.py` → pas de rebuild.
- Ajoutez une lib → `pip install` pour tester, puis `requirements.txt` + rebuild pour figer.
- Variables → `.env` + `up -d`.
- Dockerfile → rebuild.
- **Dev Container** = “run permanent” + VS Code dans le container (zéro faux imports).
