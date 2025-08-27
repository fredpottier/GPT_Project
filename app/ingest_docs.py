import os, uuid, pathlib
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from settings import settings
from retriever import embed

DOCS_DIR = "/data/docs"

def load_texts() -> List[tuple[str,str]]:
    texts = []
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            p = pathlib.Path(root) / f
            if p.suffix.lower() in {".txt", ".md", ".py", ".log"}:
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    step = 1000
                    for i in range(0, len(txt), step):
                        chunk = txt[i:i+step]
                        if chunk.strip():
                            texts.append((str(p), chunk.strip()))
                except Exception:
                    continue
    return texts

def ensure_collection(client: QdrantClient, collection: str):
    collections = [c.name for c in client.get_collections().collections]
    if collection not in collections:
        client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

def ingest(project: str):
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, settings.qdrant_collection)
    docs = load_texts()
    if not docs:
        return 0
    payloads = [{"source": src, "text": txt, "project": project} for (src, txt) in docs]
    vectors = embed([p["text"] for p in payloads])
    points = [PointStruct(id=str(uuid.uuid4()), vector=v, payload=pl) for v, pl in zip(vectors, payloads)]
    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)

if __name__ == "__main__":
    # mode CLI optionnel
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "default"
    n = ingest(project)
    print(f"Ingested {n} chunks into {settings.qdrant_collection} for project={project}")
