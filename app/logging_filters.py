# app/logging_filters.py

import contextvars
import logging
import re

# Variable de contexte pour suivre l’ID de requête
_request_id_ctx = contextvars.ContextVar("request_id", default="-")

# Appelle ceci pour lier l’ID de requête au contexte courant
def set_request_id(rid: str):
    _request_id_ctx.set(rid)

class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get()
        # Nettoyage des infos sensibles
        record.msg = redact_secrets(str(record.getMessage()))
        record.args = ()
        return True

def redact_secrets(message: str) -> str:
    patterns = [
        re.compile(r"(sk-[A-Za-z0-9]{20,})"),  # OpenAI
        re.compile(r"(?i)authorization:\s*Bearer\s+\S+"),
        re.compile(r"(?i)api[_-]?key[=:]\s*\S+")
    ]
    for pat in patterns:
        message = pat.sub("[REDACTED]", message)
    return message
