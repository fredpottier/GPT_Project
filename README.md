# 🚀 GPT Project – LangGraph + Zep + Qdrant

Ce projet fournit une **infrastructure portable** pour développer des agents IA avec **mémoire longue durée** et **recherche documentaire**. Il combine :
- **LangGraph** : orchestrateur de workflows multi-étapes avec état persistant (checkpoints).
- **Zep** : mémoire conversationnelle longue durée (stockage, résumé automatique, recherche vectorielle).
- **Qdrant** : base vectorielle pour le RAG (Recherche Augmentée par les Documents).
- **FastAPI** : API unique pour l'interaction avec l’assistant.
- **Docker Compose** : pour assurer la portabilité.
---

## 📂 Structure du projet

```
gpt-project/
├─ README.md
├─ .env.example
├─ .env
├─ docker-compose.yml
├─ scripts/
│  ├─ start.bat
│  ├─ stop.bat
│  ├─ reset.bat
│  ├─ ingest_docs.bat
├─ docker/app/Dockerfile
└─ app/
   ├─ main.py
   ├─ ...
   └─ requirements.txt
└─ data/
   ├─ ...
```

---

## ⚙️ Installation et Configuration

### Prérequis
- **Windows 10/11 avec WSL2 activé**
- **Docker Desktop** installé et en cours d’exécution
- Une **clé OpenAI** valide (`OPENAI_API_KEY`)

### Étapes
1. Copier `.env.example` vers `.env` :
```bash
cp .env.example .env
```

2. Modifier `.env` :
   - Ajouter votre `OPENAI_API_KEY`
   - Changer `APP_API_KEY` pour la sécurité

3. Démarrer les services :
```powershell
scripts\start.bat
```

---

## 📖 Utilisation et Fonctionnement

### Endpoints API Commun
1. **Vérifier l’état de l'application**
   - `GET http://localhost:5173/health`
   - Réponse : `{"status": "ok"}`

2. **Poser une Question**
   - `POST http://localhost:5173/ask`
   - Headers : `x-api-key: <APP_API_KEY>`
   - Body :
   ```json
   {
     "session_id": "mon-projet-1",
     "question": "Votre question ici"
   }
   ```

3. **Ajouter des Documents**
   - Déposez des fichiers dans `data/docs/` puis exécutez :

```powershell
scripts\ingest_docs.bat
```

### Fonctionnement
- LangGraph orchestre le flux des questions et réponses.
- Zep assure la mémoire conversationnelle.
- Qdrant stocke les informations vectorisées.

---

## 🔐 Sécurité et 🛠️ Maintenance

- Accès sécurisé via header `x-api-key`.
- Arrêter les services :

```powershell
scripts\stop.bat
```

- Réinitialiser l'état (efface toutes données) :

```powershell
scripts\reset.bat
```

- Les logs sont accessibles dans `data/logs/app.log`.

---

## 🖥️ Interface Utilisateur (UI)

L'interface utilisateur du projet, construite avec Streamlit, fournit les fonctionnalités suivantes :

### Gestion de Projets
- **Création de Projets** : Permet d'ajouter de nouveaux projets avec un nom et une couleur personnalisée.
- **Sélection de Projets** : Interface pour sélectionner un projet actif parmi ceux existants.

### Ingestion de Documents
- **Téléchargement de Fichiers** : Les utilisateurs peuvent téléverser des fichiers directement via l'interface ; formats supportés : `.txt`, `.md`, `.py`, `.log`.
- **Ingestion** : Après le téléversement, les fichiers peuvent être ingérés dans la base de données Qdrant pour le projet sélectionné à l'aide d'un simple bouton.

### Interface de Chat
- **Discussion en Temps Réel** : Une interface de chat permet aux utilisateurs d'échanger des messages textuels avec un système backend.
- **Attachement d'Images** : Les utilisateurs peuvent joindre des images à leurs messages chat.
- **Affichage de l'Historique** : Présente l'historique complet des interactions de chat, facilitant la consultation des conversations passées.

### Personnalisation
- **Visuels de Projet** : Utilisation de couleurs et de badges pour indiquer le projet actuel de manière visuelle et esthétique dans l'interface.

Cette interface offre une manière intuitive et directe d'interagir avec le système, rendant les fonctionnalités de gestion de projets et de communication facilement accessibles depuis n'importe quel navigateur web.

## Évolutions possibles et 📎 Ressources

- Intégration d'autres LLMs (Anthropic, Ollama local).
- Monitorer avec Grafana + Prometheus.

- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)
- [Zep Docs](https://docs.getzep.com/)
- [Qdrant](https://qdrant.tech/)

---

## 👨‍💻 Exemple d'appel API rapide (curl)

```bash
curl -X POST http://localhost:5173/ask \
  -H "Content-Type: application/json" \
  -H "x-api-key: change_me_local_dev" \
  -d '{"session_id":"test-1","question":"Quels fichiers ont été ingérés récemment ?"}'
```

Réponse :

```json
{"answer":"J’ai trouvé 3 fichiers ingérés récemment : README.md, main.py et ingest_docs.py."}
```
