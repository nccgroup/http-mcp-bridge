import logging
from typing import Any

def log_info(msg):
    logging.getLogger("uvicorn.info").info(msg)

def log_warning(msg):
    logging.getLogger("uvicorn.info").warning(msg)

def log_error(msg):
    logging.getLogger("uvicorn.info").error(msg)

def remove_headers(headers: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    new_headers = dict(headers)
    for key in keys:
        key = key.lower()
        if key in new_headers:
            del new_headers[key]
    return new_headers