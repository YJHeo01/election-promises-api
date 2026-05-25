from __future__ import annotations

import contextvars
import json
import logging
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from app.config import Settings, get_settings


_REQUEST_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)
_MANAGED_HANDLER_ATTR = "_election_promise_structured_handler"
_REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "credential",
    "password",
    "secret",
    "token",
    "cookie",
)
_MAX_LOG_STRING_LENGTH = 2000
_MAX_LOG_SEQUENCE_LENGTH = 50


_RESERVED_LOG_RECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_request_id(request_id: str) -> contextvars.Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


class JsonLogFormatter(logging.Formatter):
    def __init__(self, service_name: str, environment: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "environment": self.environment,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = _safe_log_value(key, value)

        if record.exc_info:
            exc_type, exc_value, _traceback = record.exc_info
            payload["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "stacktrace": self.formatException(record.exc_info),
            }

        return json.dumps(payload, ensure_ascii=False, default=str)


class TextLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id:
            return f"{message} request_id={request_id}"
        return message


def configure_logging(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    level = _log_level(settings.log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = _managed_handler(root_logger)
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)
        setattr(handler, _MANAGED_HANDLER_ATTR, True)
        root_logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(_formatter(settings))

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(level)


def _formatter(settings: Settings) -> logging.Formatter:
    if settings.log_format.lower() == "text":
        return TextLogFormatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
    return JsonLogFormatter(settings.app_name, settings.environment)


def _managed_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if getattr(handler, _MANAGED_HANDLER_ATTR, False):
            return handler
    return None


def _log_level(level_name: str) -> int:
    return getattr(logging, level_name.upper(), logging.INFO)


def _safe_log_value(key: str, value: Any) -> Any:
    if _is_sensitive_key(key):
        return _REDACTED
    if isinstance(value, Mapping):
        return {
            str(inner_key): _safe_log_value(str(inner_key), inner_value)
            for inner_key, inner_value in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            _safe_log_value(key, item)
            for item in list(value)[:_MAX_LOG_SEQUENCE_LENGTH]
        ]
    if isinstance(value, str):
        if len(value) > _MAX_LOG_STRING_LENGTH:
            return f"{value[:_MAX_LOG_STRING_LENGTH]}...<truncated>"
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
