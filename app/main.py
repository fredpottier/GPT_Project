import json, os, logging
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from graph import build_graph
from settings import settings
from logging_conf import setup_logging
from ingest_docs import ingest as ingest_qdrant

setup_logging()
log = logging.getLogger("app")
app = FastAPI(title="LangGraph+Zep+Qdrant (Projects)")

graph = build_graph()

def _auth(x_api_key: str | None):
    if not x_api_key or x_api_key != settings.app_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---- Projects registry (simple JSON) ----
def _load_projects() -> List[Dict[str,str]]:
    if not os.path.exists(settings.projects_file):
        return []
    try:
        with open(settings.projects_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_projects(projects: List[Dict[str,str]]):
    os.makedirs(os.path.dirname(settings.projects_file), exist_ok=True)
    with open(settings.projects_file, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

class ProjectCreate(BaseModel):
    name: str
    color: str  # ex: #2E86DE

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/projects")
def list_projects(x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    return {"projects": _load_projects()}

@app.post("/projects")
def create_project(p: ProjectCreate, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    prjs = _load_projects()
    if any(x["name"].lower() == p.name.lower() for x in prjs):
        raise HTTPException(status_code=400, detail="Project already exists")
    prjs.append({"name": p.name, "color": p.color})
    _save_projects(prjs)
    return {"ok": True}

class Query(BaseModel):
    session_id: str
    project: str | None = "default"
    question: str

class ChatPayload(BaseModel):
    session_id: str
    project: Optional[str] = "default"
    messages: List[Dict[str, Any]]
    thread_id: str

@app.post("/ask")
def ask(q: Query, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    state = {"session_id": q.session_id, "project": q.project, "question": q.question, "messages": None, "context": [], "answer": ""}
    result = graph.invoke(state)
    ans = result["answer"]
    log.info(f"Q[{q.project}/{q.session_id}]: {q.question}")
    return {"answer": ans}

@app.post("/chat")
def chat(payload: ChatPayload, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    log.debug(f"Received chat payload: {payload}")
    state = {
        "session_id": payload.session_id,
        "project": payload.project,
        "question": None,
        "messages": payload.messages,
        "context": [],
        "answer": "",
        "thread_id": payload.thread_id,
        "user_id": "fred"
    }
    log.debug(f"Constructed state for graph.invoke: {state}")
    result = graph.invoke(state)
    ans = result["answer"]
    log.info(f"CHAT[{payload.project}/{payload.session_id}] turn")
    return {"answer": ans}

class IngestReq(BaseModel):
    project: str | None = "default"

@app.post("/ingest")
def ingest(req: IngestReq, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    n = ingest_qdrant(project=req.project or "default")
    return {"status": "ingested", "chunks": n, "project": req.project or "default"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)

