# ... imports standards ...
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import debugpy
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

import psycopg
from psycopg_pool import ConnectionPool

from langgraph.checkpoint.postgres import PostgresSaver

from graph import build_graph
from ingest_docs import ingest as ingest_qdrant
from logging_conf import setup_logging
from logging_filters import set_request_id
from settings import settings

# === Debugger (VS Code / DevContainer)
debugpy.listen(("0.0.0.0", 5678))
print("✅ Debugger is listening on port 5678")

# === Logging
setup_logging(debug=True)
log = logging.getLogger("app")
log.info("Application startup - logging system initialized")

# === FastAPI App
app = FastAPI(title="LangGraph+Zep+Qdrant (Projects)")


@app.middleware("http")
async def inject_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    set_request_id(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


# === Typing
GraphState = Dict[str, Any]


# === Helpers
def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    val = getattr(settings, key.lower(), None)
    return val or os.getenv(key, default)


def _redact_dsn(dsn: str) -> str:
    try:
        if "://" in dsn and "@" in dsn:
            scheme, rest = dsn.split("://", 1)
            userpass, host = rest.split("@", 1)
            user = userpass.split(":")[0]
            return f"{scheme}://{user}:***@{host}"
    except Exception:
        pass
    return dsn


def resolve_pg_dsn() -> str:
    dsn = _env("CHECKPOINT_PG_DSN") or _env("POSTGRES_DSN")
    if dsn:
        return dsn
    user = _env("POSTGRES_USER", "zep")
    pwd = _env("POSTGRES_PASSWORD", "zep_password")
    db = _env("POSTGRES_DB", "zep")
    host = _env("POSTGRES_HOST", "db")
    port = _env("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}?sslmode=disable"


def ping_postgres(dsn: str) -> bool:
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                _ = cur.fetchone()
        log.debug("✅ Postgres ping OK (%s)", _redact_dsn(dsn))
        return True
    except Exception as e:
        log.error("❌ Postgres ping KO (%s): %s", _redact_dsn(dsn), e)
        return False


# === Globals
_GRAPH = None
_DSN = resolve_pg_dsn()


def init_graph_once():
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    log.info("🔁 Initialisation du PostgresSaver avec DSN")
    try:
        with PostgresSaver.from_conn_string(_DSN) as checkpointer:
            compiled = build_graph()
            _GRAPH = compiled.with_config(checkpointer=checkpointer)
            log.info("✅ Graphe initialisé avec checkpoint Postgres")
            return _GRAPH
    except Exception as e:
        log.exception("❌ Échec d'initialisation du graphe: %s", e)
        raise HTTPException(status_code=500, detail="Graph initialization failed")


@app.on_event("startup")
def on_startup():
    log.info(
        "🚀 Application startup: initializing LangGraph with Postgres checkpointing"
    )
    init_graph_once()


# === Auth + Storage
def _auth(x_api_key: str | None):
    if not x_api_key or x_api_key != settings.app_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _load_projects() -> List[Dict[str, str]]:
    if not os.path.exists(settings.projects_file):
        return []
    try:
        with open(settings.projects_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_projects(projects: List[Dict[str, str]]):
    os.makedirs(os.path.dirname(settings.projects_file), exist_ok=True)
    with open(settings.projects_file, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)


# === Pydantic Models
class ProjectCreate(BaseModel):
    name: str
    color: str


class Query(BaseModel):
    session_id: str
    project: Optional[str] = "default"
    question: str


class ChatPayload(BaseModel):
    session_id: str
    project: Optional[str] = "default"
    messages: List[Dict[str, Any]]
    thread_id: str


class IngestReq(BaseModel):
    project: Optional[str] = "default"


# === Routes
@app.get("/health")
def health():
    ok = ping_postgres(_DSN)
    return {
        "status": "ok",
        "postgres": "ok" if ok else "down",
        "checkpoint_dsn": _redact_dsn(_DSN),
        "graph_ready": _GRAPH is not None,
    }


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


@app.post("/ask")
def ask(q: Query, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    if _GRAPH is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    state: GraphState = {
        "session_id": q.session_id,
        "project": q.project or "default",
        "question": q.question,
        "messages": [],
        "context": [],
        "answer": "",
        "thread_id": "default",
        "user_id": "fred",
    }

    try:
        result = _GRAPH.invoke(state)  # type: ignore
        ans = result.get("answer", "")
        log.info(f"Q[{q.project}/{q.session_id}]: {q.question}")
        return {"answer": ans}
    except Exception as e:
        log.exception(f"Invoke failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat(payload: ChatPayload, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    log.debug(f"Received chat payload: {payload}")
    if _GRAPH is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    state: GraphState = {
        "session_id": payload.session_id,
        "project": payload.project or "default",
        "question": None,
        "messages": payload.messages,
        "context": [],
        "answer": "",
        "thread_id": payload.thread_id,
        "user_id": "fred",
    }

    ans = None
    try:
        for update in _GRAPH.stream(  # type: ignore
            state,
            config={"configurable": {"thread_id": payload.thread_id}},
            stream_mode="updates",
        ):
            if isinstance(update, dict) and "answer" in update:
                ans = update["answer"]
                log.debug({"event": "graph_final", "answer": ans})
            else:
                log.debug({"event": "graph_step", "update": update})
    except Exception as e:
        log.exception(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph error: {e}")

    return {"answer": ans or ""}


@app.post("/ingest")
def ingest(req: IngestReq, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    n = ingest_qdrant(project=req.project or "default")
    return {"status": "ingested", "chunks": n, "project": req.project or "default"}


# === Launch
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)
