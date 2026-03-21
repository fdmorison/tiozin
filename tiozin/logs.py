import logging
from typing import Any

import structlog

from . import config

_MASK = "***"
_MIN_SENSITIVE_LEN = 3
_sensitive: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    return structlog.get_logger(name)


def register_sensitive(value: str) -> None:
    if value and len(value) >= _MIN_SENSITIVE_LEN:
        _sensitive.add(value)


def _mask_secrets(logger: Any, method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    if not _sensitive:
        return event_dict

    result = {}

    for k, v in event_dict.items():
        if isinstance(v, str):
            for secret in _sensitive:
                v = v.replace(secret, _MASK)
        result[k] = v

    return result


def setup() -> None:
    logging.basicConfig(
        level=config.log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    structlog.reset_defaults()

    console_renderer = structlog.dev.ConsoleRenderer(
        colors=True,
        sort_keys=False,
        exception_formatter=structlog.dev.RichTracebackFormatter(
            show_locals=config.log_show_locals
        ),
    )

    json_renderer = structlog.processors.JSONRenderer(
        ensure_ascii=config.log_json_ensure_ascii,
    )

    structlog.configure(
        processors=[
            _mask_secrets,
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt=config.log_date_format, utc=True),
            structlog.dev.set_exc_info,
            json_renderer if config.log_json else console_renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
