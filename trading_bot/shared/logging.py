from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            payload.update(context)
        return json.dumps(payload, ensure_ascii=True)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - filter is logging API
        if not hasattr(record, "context"):
            record.context = {}
        return True


class ContextLogger:
    def __init__(self, logger: logging.Logger, context: Mapping[str, Any] | None = None) -> None:
        self._logger = logger
        self._context = dict(context or {})

    def bind(self, **context: Any) -> ContextLogger:
        merged = dict(self._context)
        merged.update(context)
        return ContextLogger(self._logger, merged)

    def _log(self, level: int, message: str, **fields: Any) -> None:
        context = dict(self._context)
        context.update(fields)
        self._logger.log(level, message, extra={"context": context})

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, **fields)

    def exception(self, message: str, **fields: Any) -> None:
        self._logger.exception(message, extra={"context": dict(self._context, **fields)})


def configure_logging(level: str | None = None, json_output: bool | None = None) -> None:
    log_level = level or os.getenv("TRADING_BOT_LOG_LEVEL", "INFO")
    json_flag = json_output
    if json_flag is None:
        json_flag = os.getenv("TRADING_BOT_LOG_JSON", "false").lower() in ("1", "true", "yes")

    root = logging.getLogger()
    root.setLevel(log_level)

    if root.handlers:
        return

    handler = logging.StreamHandler()
    if json_flag:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(context)s"
        )
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    root.addHandler(handler)


def get_logger(name: str | None = None) -> ContextLogger:
    configure_logging()
    return ContextLogger(logging.getLogger(name or "trading_bot"))
