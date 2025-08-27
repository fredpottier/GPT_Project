from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from openai import OpenAI
from settings import settings
from memory import ZepMemory
from retriever import DocsRetriever
import os

client = OpenAI(api_key=settings.openai_api_key)
docs_retriever = DocsRetriever()

class GraphState(TypedDict):
    session_id: str
    project: str | None
    question: str | None
    messages: List[Dict[str, Any]] | None
    context: List[str]
    answer: str

def node_retrieve_memory(state: GraphState) -> GraphState:
    mem = ZepMemory(session_id=state["session_id"], project=state.get("project"))
    state["context"] = mem.retrieve_context(limit=6)
    return state

def _extract_query_from_messages(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages or []):
        if m.get("role") == "user":
            parts = m.get("content") or []
            texts = [p.get("text","") for p in parts if p.get("type") == "text"]
            if texts: return texts[-1]
    return ""

def node_retrieve_docs(state: GraphState) -> GraphState:
    query = state.get("question") or _extract_query_from_messages(state.get("messages") or [])
    if not query:
        state["context"] = (state.get("context") or [])
        return state
    hits = docs_retriever.search(query=query, top_k=4, project=state.get("project") or "default")
    lines = [f"DOC: {t} (score={score:.3f})" for t, score in hits]
    state["context"] = (state.get("context") or []) + lines
    return state

def node_reason(state: GraphState) -> GraphState:
    ctx_text = "\n".join(state.get("context", []))
    system_msg = ("Tu es un assistant concis et fiable.\n"
                  "Utilise le contexte fourni quand pertinent et cite les DOCs entre crochets.\n")

    if state.get("question"):
        prompt = f"Contexte:\n{ctx_text}\n\nQuestion:\n{state['question']}\n"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system_msg},
                      {"role":"user","content":prompt}],
            temperature=0.2
        )
        state["answer"] = resp.choices[0].message.content
        return state

    messages = state.get("messages") or []
    user_text = _extract_query_from_messages(messages)
    content = [{"type":"text","text":f"Contexte:\n{ctx_text}\n\nQuestion:\n{user_text}"}]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system_msg},
                  {"role":"user","content":content}],
        temperature=0.2
    )
    state["answer"] = resp.choices[0].message.content
    return state

def node_answer(state: GraphState) -> GraphState:
    mem = ZepMemory(session_id=state["session_id"], project=state.get("project"))
    if state.get("question"):
        mem.add_messages([
            {"role":"user", "content": state["question"]},
            {"role":"assistant", "content": state["answer"]}
        ])
    else:
        last = _extract_query_from_messages(state.get("messages") or [])
        mem.add_messages([
            {"role":"user", "content": last},
            {"role":"assistant", "content": state["answer"]}
        ])
    return state


def _resolve_pg_dsn() -> str:
    """
    Priorité à CHECKPOINT_PG_DSN.
    Sinon, construit dynamiquement à partir des env (mêmes que Zep ou db).
    """
    dsn = os.getenv("CHECKPOINT_PG_DSN")
    if dsn:
        return dsn
    user = os.getenv("POSTGRES_USER", "zep")
    pwd = os.getenv("POSTGRES_PASSWORD", "zep_password")
    db = os.getenv("POSTGRES_DB", "zep")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}?sslmode=disable"


def build_graph():
    dsn = _resolve_pg_dsn()
    with PostgresSaver.from_conn_string(dsn) as checkpointer:
        graph = StateGraph(GraphState)
        graph.add_node("retrieve_memory", node_retrieve_memory)
        graph.add_node("retrieve_docs", node_retrieve_docs)
        graph.add_node("reason", node_reason)
        graph.add_node("answer", node_answer)
        graph.set_entry_point("retrieve_memory")
        graph.add_edge("retrieve_memory", "retrieve_docs")
        graph.add_edge("retrieve_docs", "reason")
        graph.add_edge("reason", "answer")
        graph.add_edge("answer", END)
        return graph.compile(checkpointer=checkpointer)

