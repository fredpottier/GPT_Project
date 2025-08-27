import base64, requests, streamlit as st, os, json, re, uuid
from typing import List, Dict, Any

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
APP_URL = os.getenv("APP_URL", "http://app:5173")
API_KEY = os.getenv("APP_API_KEY", "change_me_local_dev")

def to_data_url(file) -> str:
    b64 = base64.b64encode(file.read()).decode("utf-8")
    mime = file.type or "image/png"
    return f"data:{mime};base64,{b64}"

def parse_markdown_images(md_text: str) -> List[str]:
    return re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md_text or "")

def api_get(path: str):
    return requests.get(f"{APP_URL}{path}", headers={"x-api-key": API_KEY})

def api_post(path: str, json_body: dict):
    return requests.post(f"{APP_URL}{path}", json=json_body, headers={"x-api-key": API_KEY})

st.set_page_config(page_title="Local Chat – Projects", page_icon="📁", layout="wide")

# ---- Sidebar: Projects management ----
st.sidebar.title("📁 Projets")

# Load existing projects
resp = api_get("/projects")
projects = (resp.json().get("projects") if resp.ok else []) or []
project_names = [p["name"] for p in projects]
name_to_color = {p["name"]: p.get("color","#3B82F6") for p in projects}

with st.sidebar.expander("Créer un projet", expanded=False):
    new_name = st.text_input("Nom du projet", placeholder="ex: SAP, Perso, Médecine...")
    new_color = st.color_picker("Couleur", value="#3B82F6")
    if st.button("Créer"):
        if not new_name.strip():
            st.warning("Nom obligatoire")
        else:
            r = api_post("/projects", {"name": new_name.strip(), "color": new_color})
            if r.ok:
                st.success("Projet créé. Recharge la page pour l’afficher dans la liste.")
            else:
                st.error(r.text)

project = st.sidebar.selectbox("Projet courant", options=["default"] + project_names, index=0)
proj_color = name_to_color.get(project, "#3B82F6") if project != "default" else "#3B82F6"

# Ingestion docs pour ce projet
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Ingestion de documents")
uploaded_docs = st.sidebar.file_uploader("Déposer des fichiers (.txt, .md, .py, .log)", accept_multiple_files=True, type=["txt","md","py","log"])
if st.sidebar.button("Ingest dans Qdrant (projet courant)"):
    docs_dir = "/data/docs"
    os.makedirs(docs_dir, exist_ok=True)
    for f in uploaded_docs or []:
        with open(os.path.join(docs_dir, f.name), "wb") as out:
            out.write(f.getbuffer())
    r = api_post("/ingest", {"project": project})
    if r.ok:
        st.sidebar.success(f"Ingestion ok ({r.json().get('chunks',0)} chunks) pour {project}")
    else:
        st.sidebar.error(f"Erreur ingestion: {r.text}")

# ---- Header / Badge projet ----
st.markdown(f"""
<style>
.badge {{
  padding: 6px 10px;
  border-radius: 999px;
  border: 2px solid {proj_color};
  color: {proj_color};
  font-weight: 600;
}}
.chatbox-border > div:nth-child(1) {{
  border: 2px solid {proj_color} !important;
  border-radius: 12px;
  padding: 6px;
}}
</style>
""", unsafe_allow_html=True)
st.markdown(f"<div class='badge'>Projet : {project}</div>", unsafe_allow_html=True)

st.title("💬 Chat local (API only)")

# ---- Chat state ----
if "history" not in st.session_state:
    from typing import cast
    st.session_state.history = cast(List[Dict[str, Any]], [])

st.sidebar.markdown("---")
st.sidebar.subheader("🖼️ Joindre des images au prochain message")
image_files = st.sidebar.file_uploader("Images (jpg/png)", accept_multiple_files=True, type=["png","jpg","jpeg"])

# Render history
with st.container():
    for turn in st.session_state.history:
        with st.chat_message(turn["role"]):
            texts = [p["text"] for p in turn["content"] if p["type"] == "text"]
            if texts:
                st.markdown(texts[-1])
            imgs = [p["data_url"] for p in turn["content"] if p["type"] == "image"]
            for data_url in imgs:
                st.image(data_url)

prompt = st.chat_input("Écris ton message…")
if prompt:
    user_parts = [{"type":"text","text":prompt}]
    for img in image_files or []:
        user_parts.append({"type":"image","data_url": to_data_url(img)})
    st.session_state.history.append({"role":"user","content":user_parts})

    payload = {
        "session_id": "ui-session",
        "project": project,
        "thread_id": st.session_state["thread_id"],
        "messages": st.session_state.history
    }

    # Afficher temporairement le thread_id et le payload
    st.write(f"Thread ID: {st.session_state['thread_id']}")
    st.write("Payload:", payload)
    r = api_post("/chat", payload)
    if not r.ok:
        with st.chat_message("assistant"):
            st.error(f"Erreur API: {r.status_code} {r.text}")
    else:
        answer = r.json().get("answer","")
        st.session_state.history.append({"role":"assistant","content":[{"type":"text","text":answer}]})
        with st.chat_message("assistant"):
            st.markdown(answer)
            for url in parse_markdown_images(answer):
                st.image(url)

