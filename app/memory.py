from zep_python.client import Zep
from zep_python import RoleType
from settings import settings
from typing import List, Dict


class ZepMemory:
    def __init__(self, session_id: str, project: str | None):
        self.session_id = f"{project or 'default'}::{session_id}"
        self.client = Zep(
            base_url=settings.zep_api_url,  # Peut être None si ZEP_API_URL est dans l'env
            api_key=settings.zep_api_key    # Peut être None si ZEP_API_KEY est dans l'env
        )
        try:
            # add() accepte un dictionnaire directement
            self.client.user.add({"user_id": self.session_id})
        except Exception:
            pass

    def add_messages(self, messages: List[Dict[str, str]]):
        zep_msgs = [
            {
                "role": "user" if m["role"] == "user" else "assistant",
                "content": m["content"]
            }
            for m in messages
        ]
        self.client.memory.add_messages(
            session_id=self.session_id,
            messages=zep_msgs,
            memory_type="chat"
        )

    def retrieve_context(self, limit: int = 6) -> List[str]:
        payload = {
            "session_id": self.session_id,
            "memory_type": "chat",
            "search_scope": "messages",
            "top_k": limit
        }
        response = self.client.memory.search_memory(payload)
        return [msg.content for msg in response.messages]
