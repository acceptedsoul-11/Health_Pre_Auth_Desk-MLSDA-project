"""
Structured logging configuration using structlog.
Emits JSON in production, colored text in development.
Every log entry carries correlation_id and run_id for full traceability.
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

from app.core.config import get_settings

# ── Context variables for cross-service correlation ─────────────────────────
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_run_id: ContextVar[str] = ContextVar("run_id", default="")


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_run_id(rid: str) -> None:
    _run_id.set(rid)


def get_run_id() -> str:
    return _run_id.get()


def _add_context(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Processor: inject correlation and run IDs into every log entry."""
    cid = _correlation_id.get()
    rid = _run_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    if rid:
        event_dict["run_id"] = rid
    return event_dict


def configure_logging() -> None:
    settings = get_settings()
    is_dev = settings.app_env == "development"

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _add_context,
    ]

    if is_dev:
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Silence noisy libraries
    for lib in ("uvicorn.access", "celery.utils.functional"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
