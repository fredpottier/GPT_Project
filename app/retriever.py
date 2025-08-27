from typing import List, Tuple, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
from settings import settings

# Modèle d'embeddings OpenAI (1536 dims)
EMBED_MODEL = "text-embedding-3-small"

# Client OpenAI pour les embeddings
_client_openai = OpenAI(api_key=settings.openai_api_key)


def embed(texts: List[str]) -> List[List[float]]:
    """
    Calcule les embeddings OpenAI pour une liste de textes.
    Retourne une liste de vecteurs (List[float]) de taille 1536.
    """
    if not texts:
        return []
    res = _client_openai.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in res.data]


class DocsRetriever:
    """
    Récupération de passages pertinents dans Qdrant (RAG).
    Les points doivent avoir un payload au minimum :
      {
        "text":   <chunk de texte>,
        "source": <chemin/nom de fichier>,
        "project": <nom du projet>
      }

    Utilisation :
        r = DocsRetriever()
        results = r.search("ma question", top_k=5, project="SAP")
        # results -> List[(formatted_text, score)]
    """

    def __init__(self, collection: Optional[str] = None):
        self.collection = collection or settings.qdrant_collection
        self.client = QdrantClient(url=settings.qdrant_url)

    def search(
        self,
        query: str,
        top_k: int = 5,
        project: Optional[str] = None,
        with_scores: bool = True,
    ) -> List[Tuple[str, float]]:
        """
        Recherche sémantique dans la collection Qdrant.
        - query : texte de la requête
        - top_k : nb de résultats à retourner
        - project : filtre strict sur le projet (payload.project == project)
        - with_scores : retourne le score de similarité de Qdrant

        Retour : liste de tuples (texte_formatté, score)
        """
        if not query.strip():
            return []

        q_emb = embed([query])[0]

        q_filter = None
        if project:
            q_filter = Filter(must=[FieldCondition(key="project", match=MatchValue(value=project))])

        hits = self.client.search(
            collection_name=self.collection,
            query_vector=q_emb,
            limit=top_k,
            query_filter=q_filter,
            with_payload=True,
            with_vectors=False,
        )

        results: List[Tuple[str, float]] = []
        for h in hits:
            payload = h.payload or {}
            txt = (payload.get("text") or "").strip()
            src = payload.get("source") or ""
            # Format simple : [source] texte
            formatted = f"[{src}] {txt}" if src else txt
            score = float(h.score) if with_scores else 0.0
            results.append((formatted, score))

        return results
