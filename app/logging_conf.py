# app/logging_conf.py

import logging
import sys
import os
from logging.config import dictConfig

from logging_filters import RequestContextFilter  # <= Import ici

LOG_DIR = os.getenv("LOG_DIR", "/data/logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging(debug: bool = False):
    level = "DEBUG" if debug else "INFO"
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
            }
        },
        "filters": {
            "request_context": {
                '()': RequestContextFilter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_context"],
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": LOG_FILE,
                "maxBytes": 10_000_000,
                "backupCount": 3,
                "formatter": "default",
                "filters": ["request_context"],
                "encoding": "utf-8"
            },
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"]
        },
    })
